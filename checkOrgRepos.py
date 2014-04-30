__author__ = 'jotegui'

import extractStats
from datetime import datetime
from util import get_org_repo

lapse = 'month'
testing = False
today = datetime.now()

pubs = extractStats.main(today=today, lapse=lapse, testing=testing)
repos = pubs.keys()
for i in repos:
    #print i, pubs[i]['url']
    try:
        get_org_repo(pubs[i]['url'])
    except:
        print 'URL not found: {0}\nPub: {1}'.format(pubs[i]['url'], i)