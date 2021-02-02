# commit-que-devel-days-202

A few examples of how to use NSO commit queues and NSO commit queue flags

# Purpose

The purpose of this example is provide a few examples of how best to utilze NSO commit
queues. All of the examples utlize an NSO instance installed w/default settings. All commit
queue operations are done utlizing the JSON RPC API

# Documentation

Appart from this file, the main documentation is the python code itself

# Dependencies

In order to utilize all the functionality, you will need to have (in the path)
the following components.

* NSO 5.3.2+
* Python or 3+
* Cisco IOS-XR NED

# Build instructions

   Download and uncompress a copy of the cisco-iosxr CLI NED and place in the
   device-node/packages directory and rename the ned to cisco-iosxr.

   If you with to run through the rollback and error scenarios then you will
   need to copy a version of the cisco-ioxr CLI NED to a directory at the top 
   level. So executing something like the following:

       cp -r packages/cisco-iosxr cisco-iosxr-broken

   After the copy is completed the "broken" version needs to be modified by
   making a small change to the YANG file. In an editor modify the hostname setting
   from the following
<pre>

  /// ========================================================================
  /// hostname
  /// ========================================================================

  leaf hostname {
    tailf:info "Set system's network name";
    type string {
      tailf:info "WORD;;This system's network name";
    }
  }
</pre>
   To the following:
<pre>
  /// ========================================================================
  /// hostname
  /// ========================================================================

  leaf hostname {
    tailf:info "Set system's network name";
    type string {
      tailf:info "WORD;;This system's network name";
      length "1..16";
    }
  }
</pre>


   from the top level directory simply type the following:

   make clean all

# Running the demonstration

## Execute the reconcile demonstration
  First start up the simulation and the netsim devices

  make start

  Properly set PYTHONPATH variable

  export $PATHPATH="$PWD/code"

  or 

  set $PYTHONPATH="$PWD/nsop"

  Change directory to the NSOP director and type 
 
  python nsop.py  
  
  You can log into the GUI by using the following URL
  htpp://127.0.0.1:4000

  Username admin
  Password admin
  
  Click on System and then Commit Queues

  The commit queue page doesn't auto upate so you will need to refresh it to see updates.

### Step(1) List the available scenarios
<pre>
   commit-que-devel-days-2020 % python que.py -l

		Current Loaded Scenarios
		--------------------------
		APPLY-DEVICE-TEMPLATE
		ATOMIC
		BUNDLING
		NO-OVERLAP
		OVERLAP
		ROLLBACK-ON-ERROR
		SYNC-ASYNC

   commit-que-devel-days-2020 %

</pre>
### Step(2) Select a particular scenario and run it
<pre>

dan@DANISULL-M-73NJ commit-que-devel-days-2020 % python que.py -s NO-OVERLAP

Starting NSO Commit Queue No Overlap

	Step(1): Stop netsim devices ............................................................. Complete
	Step(2): Create Service Instance A ....................................................... Complete

		<config xmlns="http://tail-f.com/ns/config/1.0">
		  <intf xmlns="http://com/example/intf">
		    <name>TEST-NO-OVERLAP-A</name>
		    <device>r01</device>
		    <interfaces>
		      <id>0/3/0/0</id>
		      <description>TEST-NO-OVERLAP-A</description>
		    </interfaces>
		  </intf>
		</config>
		
	Step(3): Commit Changes (A) .............................................................. Complete

		Commit Option Settings
		---------------------------------------------
		commit-queue              : async
		commit-queue-atomic       : true
		commit-queue-tag          : Service (A)

		commit-queue id: 1593457321745

	Step(4): Create Service Instance B ....................................................... Complete

		<config xmlns="http://tail-f.com/ns/config/1.0">
		  <intf xmlns="http://com/example/intf">
		    <name>TEST-NO-OVERLAP-B</name>
		    <device>r01</device>
		    <interfaces>
		      <id>0/3/0/1</id>
		      <description>TEST-NO-OVERLAP-B</description>
		    </interfaces>
		  </intf>
		</config>
		
	Step(5): Commit Changes (B) .............................................................. Complete

		Commit Option Settings
		---------------------------------------------
		commit-queue              : async
		commit-queue-atomic       : true
		commit-queue-tag          : Service (B)

		commit-queue id: 1593457322192

	Step(6): Display Commit Queue(s) ......................................................... Complete

		Commit Queue Entries: (2)

		ID               Tag                  Age    Status     Atomic Devices
		---------------- -------------------- ------ ---------- ------ --------------------
		1593457321745    Service (A)          0      executing  true   r01         
		1593457322192    Service (B)          0      waiting    true   r01         


	Step(7): Check commit queue(s) ........................................................... Complete

		Verify commit-queue(s) and hit return to continue : 

	Step(8): Start netsim devices ............................................................ Complete
	Step(9): Wait for commit queues to drain ................................................. Complete
	Step(10): Display Commit Queue Complete .................................................. Complete

		ID               Tag                  Status     Failed Devices Completed Device(s)
		---------------- -------------------- ---------- -------------- ------------------------
		1593457321745    Service (A)          completed                 r01             
		1593457322192    Service (B)          completed                 r01             

	Step(11): Cleanup (delete intf services A&B)  ............................................ Complete
	Step(12): Commit Cleanup Operation(s) .................................................... Complete

Finished NSO Commit Queue No Overlap

commit-que-devel-days-2020 %
</pre>
