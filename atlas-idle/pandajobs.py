# *****************************************************************************
# Get jobs from PANDA for appropriate groups (non-grid)
# All modules must have the get_jobs() method that returns a mapping of
# group-name -->  num_idle
#
# William Strecker-Kellogg <willsk@bnl.gov>
# *****************************************************************************

import requests
import cPickle
import logging

log = logging.getLogger()


# Queues to watch, map of PANDA Name -> Condor Group name
queues = {
    'BNL_PROD_MCOREHIMEM': 'group_atlas.prod.xl',
    'BNL_PROD_MCORE':  'group_atlas.prod.mp',
    'BNL_ATLAS_2':     'group_atlas.prod.test',
    'BNL_PROD':        'group_atlas.prod.production',
    'ANALY_BNL_SHORT': 'group_atlas.analysis.short',
    'ANALY_BNL_LONG':  'group_atlas.analysis.long',
    'ANALY_BNL_MCORE': 'group_atlas.analysis.amc',
}

# **************** Configuration variables and information *****************
url = "https://pandaserver.cern.ch:25443/server/panda/getJobStatisticsWithLabel"

# According to J. Hover, this is the definitive test for if a queue is analysis
is_analysis = lambda q: q.startswith("ANALY")


def get_num_activated(queue, data):
    # Production queues are under 'managed', analysis under 'user', just the
    # way it is in PANDA, go figure!?

    key = 'user' if is_analysis(queue) else 'managed'
    if 'activated' in data.get(key, {}):
        return data[key]['activated']
    else:
        return 0


def get_jobs():
    log.info("Accessing panda at %s", url)
    try:
        webreq = requests.get(url, verify=False, stream=True)
        # This is so horribly insecure, I can't believe it!
        webdata = cPickle.load(webreq.raw)

    except requests.exceptions.RequestException:
        log.exception("Timeout accessing PANDA webservice, exit...")
        return None

    idle = {}

    for panda_q, data in ((x, webdata.get(x)) for x in queues):
        if not data:
            log.warning("queue %s not found but not used either", panda_q)
            idle[queues[panda_q]] = 0
            continue
        else:
            log.debug("PANDA queue %s: %s", panda_q, data)

        n = get_num_activated(panda_q, data)
        log.debug("%s:%s has %d activated", panda_q, queues[panda_q], n)

        idle[queues[panda_q]] = n

    return idle

if __name__ == '__main__':
    logging.basicConfig()
    s = get_jobs()
    print(s)

