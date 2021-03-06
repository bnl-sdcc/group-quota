#!/bin/env python
# *****************************************************************************
# Get jobs from the local Condor pool for appropriate groups (non-grid)
# All modules must have the get_jobs() method that returns a mapping of
# group-name -->  num_idle
#
# William Strecker-Kellogg <willsk@bnl.gov>
# John Hover  <jhover@bnl.gov>
# *****************************************************************************
#  get_jobs() -> {'group_atlas.prod.production': 0, 
#                 'group_atlas.prod.mp': 4144, 
#                 'group_atlas.analysis.amc': 6, 
#                 'group_atlas.prod.test': 0, 
#                 'group_atlas.prod.xl': 0, 
#                 'group_atlas.analysis.long': 19599, 
#                 'group_atlas.analysis.short': 16626
#                 }
#
#import sys
#sys.path.append('/usr/lib64/python2.7/site-packages')

import libfactory
import logging
from pprint import pprint
from libfactory.htcondorlib import HTCondorSchedd, HTCondorPool
from libfactory.info import StatusInfo, IndexByKey, AnalyzerFilter, AnalyzerMap, Count

from gq import config as gqconfig

# Queues to watch 
GROUPS = {
    'group_atlas.prod.xl': 1,
    'group_atlas.prod.mp': 1,
    'group_atlas.prod.test': 1,
    'group_atlas.prod.production': 1,
    'group_atlas.analysis.short': 1,
    'group_atlas.analysis.long': 1,
    'group_atlas.analysis.amc': 1,
    }

class StripUserMap(AnalyzerMap):
    def map(self, job):
        try:
            agv = job['accountinggroup']
            if len(agv) > 3:
                agv = '.'.join(agv.split('.')[:-1])
                job['accountinggroup'] = agv
        except:
            pass
        return job
        
class IdleOnlyFilter(AnalyzerFilter):
    def filter(self, job):
        isidle = False
        try:
            jobstatus = int(job['jobstatus'])
            if jobstatus == 1:
                isidle = True
        except:
            pass
        return isidle


class AtlasOnlyFilter(AnalyzerFilter):
    def filter(self, job):
        matches = False
        try:
            ag = job['accountinggroup']
            v = GROUPS[ag]
            matches = True
        except:
            matches = False
        return matches
        
    
def get_jobs():
    jobdict = {}
    try:
        cm_host = gqconfig.condor_cm.split(':')[0]
        cm_port = gqconfig.condor_cm.split(':')[1]         
    
        pool = HTCondorPool(hostname=cm_host, port=cm_port)
        #sd = HTCondorSchedd()
        attlist = ['accountinggroup','jobstatus','xcount']
        cq = pool.condor_q(attribute_l = attlist)
        si = StatusInfo(cq)
        idlefilter = IdleOnlyFilter()  
        stripusermap = StripUserMap()
        atlasfilter = AtlasOnlyFilter()
        si = si.filter(idlefilter)
        si = si.map(stripusermap)
        si = si.filter(atlasfilter)
        si = si.indexby(IndexByKey('accountinggroup'))   
        si = si.process(Count())
        jobdict = si.getraw()
    except:
        pass
    
    return jobdict
        


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    pprint(get_jobs())




    