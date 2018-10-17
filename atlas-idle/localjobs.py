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
import sys
sys.path.append('/usr/lib64/python2.7/site-packages')

import libfactory
from pprint import pprint
from libfactory.htcondorlib import HTCondorSchedd
from libfactory.info import StatusInfo, IndexByKey, AnalyzerFilter, Count

# Queues to watch, map of PANDA Name -> Condor Group name
GROUPS = [
    'group_atlas.prod.xl',
    'group_atlas.prod.mp',
    'group_atlas.prod.test',
    'group_atlas.prod.production',
    'group_atlas.analysis.short',
    'group_atlas.analysis.long',
    'group_atlas.analysis.amc',
    ]

class IdleOnlyFilter(AnalyzerFilter):
    def filter(self, job):
        jobstatus = int(job['jobstatus'])
        return jobstatus == 1

class AtlasOnlyFilter(AnalyzerFilter):
    def filter(self, job):
        ag = job['accountinggroup']
        return 'group_atlas' in ag
    
def get_jobs():      
    sd = HTCondorSchedd()
    attlist = ['accountinggroup','jobstatus','xcount']
    cq = sd.condor_q(attribute_l = attlist, globalquery=True)
    si = StatusInfo(cq)
    idlefilter = IdleOnlyFilter()  
    atlasfilter = AtlasOnlyFilter()
    si = si.filter(idlefilter)
    si = si.filter(atlasfilter)
    si = si.indexby(IndexByKey('accountinggroup'))   
    si = si.process(Count())
    return si.getraw()


if __name__ == '__main__':
    pprint(get_jobs())




    