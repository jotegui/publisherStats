#!/usr/bin/python

import logging
from datetime import datetime
import extractStats
import pickle
# from monthlyStatReports import apikey

__author__ = 'jotegui'

today = datetime.now()

file_name = '/home/jotegui/VertNet/PublisherStats/pubs_{0}.pk'.format(format(today, '%Y_%m_%d'))

logging.basicConfig(filename='/home/jotegui/VertNet/PublisherStats/logs/to_local_{0}.log'.format(format(today, '%Y_%m_%d')),
                    format='%(levelname)s:%(asctime)s %(message)s', level=logging.DEBUG)

lapse = 'month'
testing = False
# key = apikey(testing)
# beta = True

pubs = extractStats.main(today=today, lapse=lapse, testing=testing)

# Piece of code to store pubs in disk (to avoid 1h+ of downloads)
logging.info('Writing to local file pubs_{0}.pk'.format(format(today, '%Y_%m_%d')))
with open(file_name, 'wb') as output:
    pickle.dump(pubs, output, pickle.HIGHEST_PROTOCOL)

# reports, models = generateReports.main(pubs=pubs, lapse=lapse, today=today)
#
# reports, models = betaTesting(reports=reports, models=models, beta=beta)
# models = addOrgRepoToModels(models)
# storeModels(models = models, key = key, testing = testing)
