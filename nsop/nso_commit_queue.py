#
# Copyright 2013 Tail-f Systems
#
#(C) 2017 Tail-f Systems

import json
import nso_api

qqColors = ['bg-primary',
            'bg-success',
            'bg-danger',
            'bg-aqua',
            'bg-gray',
            'bg-orange',
            'bg-navy',
            'bg-yellow'
            ]

class CommitQueue:

    def __init__(self, session):
      self.nso = session
      return


    def getQueComplete(self):

      
        path = "/ncs:devices/commit-queue/completed"
        query_info = ['id', 'tag', 'when', 'status', 'devices']
        data = self.nso.simple_query(path,
                                     "queue-item",
                                     query_info) 
        cqc = [dict(zip(query_info, values)) for values in data['result']['results']]
        
        for cq in cqc:
           dpath = "/ncs:devices/commit-queue/completed/queue-item{%s}" % cq['id']
           cq['devices'] = ','.join(self.nso.getValue(dpath + "/devices"))
          
           data = self.nso.simple_query(dpath, "failed", ['name'])
           fdata  = [item for sublist in data['result']['results'] for item in sublist]
           cq['failed-devices'] = ','.join(fdata)
          
        return cqc[::-1]

    def getQueActive(self):

        query_info = ['id', 'age', 'tag','status', 'devices','waiting-for', 'is-atomic']
        data = self.nso.simple_query('/ncs:devices/commit-queue','queue-item', query_info)
        cqi = [ dict(zip(query_info, values)) for values in data['result']['results']]
        for cq in cqi:
          s = ','
          res = self.nso.getValue("/devices/commit-queue/queue-item{%s}/devices" % cq['id'])
          s = s.join(res)
          cq['devices'] = s

        i=0
        for cq in cqi:
           cq['color'] = qqColors[i]
           if i < len(qqColors):
             i += 1
           else:
             i=0
          
        return cqi[::-1]

    def getQueLengths(self):

        path = '/ncs:devices'
        query_info = ['name','commit-queue/queue-length'] 
        
        dat = self.nso.simple_query('/ncs:devices', 
                                    'device', 
                                    query_info)
        
        data = dat['result']['results']
        cql = [ dict(zip(query_info, values)) for values in data]
        
        return cql


  
      

