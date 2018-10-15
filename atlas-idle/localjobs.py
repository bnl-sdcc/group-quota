# *****************************************************************************
# Get jobs from the local Condor pool for appropriate groups (non-grid)
# All modules must have the get_jobs() method that returns a mapping of
# group-name -->  num_idle
#
# William Strecker-Kellogg <willsk@bnl.gov>
# John Hover  <jhover@bnl.gov>
# *****************************************************************************
#
#
#  get_jobs() -> {'group_atlas.prod.production': 0, 
#                 'group_atlas.prod.mp': 4144, 
#                 'group_atlas.analysis.amc': 6, 
#                 'group_atlas.prod.test': 0, 
#                 'group_atlas.prod.xl': 0, 
#                 'group_atlas.analysis.long': 19599, 
#                 'group_atlas.analysis.short': 16626
#                 }


import requests
import cPickle
import logging
import libfactory
from libfactory.htcondorlib import HTCondorSchedd
from libfactory.info import StatusInfo, IndexByKey, AnalyzerFilter, Count

class IdleOnlyFilter(AnalyzerFilter):
        def filter(self, job):
            jobstatus = int(job['jobstatus'])
            return jobstatus == 1

log = logging.getLogger()

# Queues to watch, map of PANDA Name -> Condor Group name
groups = [
    'group_atlas.prod.xl',
    'group_atlas.prod.mp',
    'group_atlas.prod.test',
    'group_atlas.prod.production',
    'group_atlas.analysis.short',
    'group_atlas.analysis.long',
    'group_atlas.analysis.amc',
    ]

def get_jobs():      
    sd = HTCondorSchedd()
    attlist = ['accountinggroup','jobstatus','xcount']
    
    cq = sd.condor_q(attribute_l = attlist)
    myinfostatus = StatusInfo(cq)
    myfilter = IdleOnlyFilter()  
    myinfostatus = myinfostatus.filter(myfilter)
    myinfostatus = myinfostatus.indexby(IndexByKey('accountinggroup'))   
    myinfostatus = myinfostatus.process(Count())
    return myinfostatus.getraw()





    