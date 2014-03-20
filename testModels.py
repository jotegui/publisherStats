import logging
from datetime import datetime
import extractStats
import generateReports
from monthlyStatReports import apikey
from uploadToGithub import betaTesting, addOrgRepoToModels, storeModels

__author__ = 'jotegui'

today = datetime.now()
logging.basicConfig(filename='logs/models_{0}.log'.format(format(today, '%Y_%m_%d')),
                    format='%(levelname)s:%(asctime)s %(message)s', level=logging.DEBUG)
#logging.basicConfig(format='%(levelname)s:%(asctime)s %(message)s', level=logging.DEBUG)

lapse = 'month'
testing = False
key = apikey(testing)
beta = True

# pubs = extractStats.main(today=today, lapse=lapse, testing=testing)

# Piece of code to store pubs in disk (to avoid 1h+ of downloads)
import pickle
# with open('pubs_2014_02_b.pk', 'wb') as output:
#     pickle.dump(pubs, output, pickle.HIGHEST_PROTOCOL)

with open('pubs_2014_02_b.pk', 'rb') as input:
    pubs = pickle.load(input)

reports, models = generateReports.main(pubs=pubs, lapse=lapse, today=today)

reports, models = betaTesting(reports=reports, models=models, beta=beta)
models = addOrgRepoToModels(models)
storeModels(models = models, key = key, testing = testing)