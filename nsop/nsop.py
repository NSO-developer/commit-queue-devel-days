#!/usr/bin/env python3

from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for, jsonify
from flask_cors import CORS
import os
import sys
import json
import logging
import argparse
from nso_api import NsoSession as nso
from nso_devices_api import nsoDevices as nsdev
from nso_dashboard_api import nsoDashboard as nsodash
from nso_commit_queue import CommitQueue
import time
from datetime import datetime, time

app = Flask(__name__)

nsoDefaultHost = ""
nsoc = {}
vinfo = {}

@app.route('/', methods=['GET', 'POST'])
def home():
       if not 'logged_in' in session:
          return redirect(url_for('login')) 
       else:
          return redirect(url_for('dashboard'))


@app.route('/dry-run', methods=['POST'])
def dry_run():
        if not 'logged_in' in session:
          return redirect(url_for('login')) 
        nscc = nsoc[session['id']]  
        ###
        # validate the changes
        ###
        outformat = request.form['outformat']
        result = nscc.dryRun(outformat)

        if result :
          return jsonify({'status' : 'ok',
                          'result' : result})

        return jsonify({'status' : 'ok',
                        'result' : "No dry-run data provided"})

@app.route('/revert', methods=['POST'])
def revert():
        if not 'logged_in' in session:
          return redirect(url_for('login'))

        nscc = nsoc[session['id']]
        if (nscc.is_modified() == True):

          if (nscc.revert() == False):
             return jsonify({'error' : 'NSO Failed to abort transaction'})

        return jsonify({'status' : 'ok'})

@app.route('/commit', methods=['POST'])
def commit():
        if not 'logged_in' in session:
          return redirect(url_for('login')) 
        nscc = nsoc[session['id']]  

        result = nscc.validateCommit()
        
        if result == False:
          return jsonify({'status' : 'failed',
                          'error' : "validate_failure"})
        else:
          result = nscc.commit()
          if result == False:
           return jsonify({'status' : 'failed',
                          'error' : "validate_failure"})

        return jsonify({'status' : 'ok'})        

@app.route('/devices', methods=['GET', 'POST'])
def devices():
       if not 'logged_in' in session:
          return redirect(url_for('login')) 
       else:
         nscc = nsoc[session['id']]
         nsod = nsodash(nscc)
         system = nsod.systemInfo()
         devs = nsod.devicesInfo()
         nedinfo = nsdev.getNedInfo()
         return render_template('devices.html',
                                 nedinfo=nedinfo,
                                 devices=devs,
                                 system=system)


@app.route('/devices/action', methods=['POST'])
def devicesAction():
        if not 'logged_in' in session:
          return redirect(url_for('login')) 
        nscc = nsoc[session['id']]     
        ndev = nsdev(nscc)
        result = ndev.deviceAction(request.form['action'],
                                   request.form['devices'])
        return jsonify({'result' : result})

@app.route('/devices/add-device', methods=['POST'])
def devicesAdd():
        if not 'logged_in' in session:
          return redirect(url_for('login')) 
        nscc = nsoc[session['id']]     
        ndev = nsdev(nscc)
        devParams = {}
        devParams['name'] = request.form['name']
        devParams['address'] = request.form['address']
        devParams['port'] = request.form['port']
        devParams['state'] = request.form['state']
        devParams['devtype'] = request.form['devtype']
        devParams['authgroup'] = request.form['authgroup']
        result = ndev.deviceAdd(devParams)

        if result == True :
          return jsonify({'status' : 'failed'})
        return jsonify({'status' : 'ok'})

@app.route('/devices/del-device', methods=['POST'])
def devicesDel():
        return jsonify({'status' : 'completed'})

@app.route('/dashboard', methods=['GET'])
def dashboard():
       if not 'logged_in' in session:
          return redirect(url_for('login'))
       ###
       # Read devices device info from NSO
       ###
       nscc = nsoc[session['id']]
       nsod = nsodash(nscc)
       ###
       # Load package information
       ###
       packages = nsod.packageInfo()
       system = nsod.systemInfo()
       users = nsod.usersInfo()
       alarms = nsod.alarmInfo()
       srvinfo = nsod.serviceInfo()
       devinfo = nsod.deviceSummary()
       pvmi = nsod.pythonInfo()
       return render_template('dashboard.html', packages=packages,
                                                system=system,
                                                users=users,
                                                alarms=alarms,
                                                srvinfo=srvinfo,
                                                pvmi=pvmi,
                                                devinfo=devinfo)
@app.route('/rollbacks/load', methods=['POST'])
def rollbacksLoad():
        if not 'logged_in' in session:
          return redirect(url_for('login'))
        nscc = nsoc[session['id']] 
        fileNum = request.form['nr']
        result = nscc.load_rollback(int(fileNum))
        return jsonify({'status' : 'ok'})

@app.route('/rollbacks', methods=['GET'])
def rollbacks():
       if not 'logged_in' in session:
          return redirect(url_for('login'))
       nscc = nsoc[session['id']]
       data = nscc.get_rollbacks()
       nsod = nsodash(nscc)
       system = nsod.systemInfo()
       rollbacks = {}
       if 'rollbacks' in data:
         rollbacks = data['rollbacks'] 

       return render_template('rollbacks.html', 
                              system=system,
                              rollbacks=rollbacks)

@app.route('/commitqueue', methods=['GET'])
def commitQueue():
       if not 'logged_in' in session:
          return redirect(url_for('login'))
       nscc = nsoc[session['id']]
       nsod = nsodash(nscc)
       system = nsod.systemInfo()
       cq = CommitQueue(nscc)
       cql = cq.getQueLengths()
       cqd = cq.getQueActive()
       cqc = cq.getQueComplete()

       return render_template('commitqueue.html', 
                              system=system,
                              qLen =cql,
                              qData = cqd,
                              qCData = cqc)

@app.route('/logout', methods=['GET'])
def logout():
       ###
       # Log out of NSO and the portal
       ###
       if not 'logged_in' in session:
          return redirect(url_for('login'))
       if session['logged_in'] == True:
         session['logged_in'] = False;
         nsoc[session['id']].logout()

       return redirect(url_for('login'))

@app.route('/login', methods=['POST', 'GET'])
def login():
       ##
       # Post operation means someone filled out the login form
       ##
       if request.method == 'POST':
         ###
         # Remove saved information
         ###
         session.pop('logged_in', None)
         session['id'] = str(os.urandom(12))
         session['change_set'] = "none"

         ###
         # Attempt to login to NSO
         ###
         user = request.form['username']
         pswd = request.form['password']
         host = request.form['host']
         port = request.form['port']
         
         if  not user:
            print('NSOP login credentails: defaulting to admin/admin')
            user = pswd = 'admin'
         ###
         # If the login page specifies a NSO address use that
         # otherwise stick to the default host provided @startup
         ###
         nso_server = nsoDefaultHost
         if (host != ''):
           nso_server = host
         if (port == ''):
            port = 8080

         nsoc[session['id']] = nso(nso_server, session, user, pswd, port=port, debug=True)
         session['user'] = user
         session['logged_in'] = nsoc[session['id']].login(user, pswd)

         if session['logged_in'] == True:
            print('User [%s] Logged into NSO instance' % (user))
            ###
            # Open a read_write transaction
            ###
            nsoc[session['id']].getNewTrans('read_write')

            return redirect(url_for('home'))
         
         return redirect(url_for('login'))

       else:
         return render_template('login.html')
 
def main(agrv):
    global nsoDefaultHost

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action='store_true', dest='debug', default=True, help="Enable debug mode")
    parser.add_argument("-p", "--port", action="store", dest='port', nargs='?', type=int, default=4000, help="Configure NSOP port (default=4000)")
    parser.add_argument("-s", "--server", action="store", dest='server', nargs='?', default='127.0.0.1', help="Configure NSOP host default=localhost")
    args = parser.parse_args()
    
    ###
    # Set the global host value which will be the default
    # host/ip address to connect to.
    ###
    nsoDefaultHost = args.server 

    ###
    # Start up flask application
    ###
    app.secret_key = os.urandom(12)
    app.run(debug=args.debug,host='0.0.0.0', port=args.port)

if __name__ == "__main__":
    main(sys.argv[1:])
