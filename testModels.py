import logging
from datetime import datetime
import extractStats
import generateReports
from monthlyStatReports import apikey
from uploadToGithub import betaTesting, addOrgRepoToModels, storeModels

__author__ = 'jotegui'

logging.basicConfig(filename='logs/models_{0}.log'.format(format(datetime.now(), '%Y_%m_%d')), format='%(levelname)s:%(asctime)s %(message)s', level=logging.DEBUG)

lapse = 'month'
testing = True
key = apikey(testing)
beta = True

pubs = extractStats.main(lapse = lapse, testing = testing)
reports, models = generateReports.main(pubs, lapse)

reports, models = betaTesting(reports = reports, models = models, beta = beta)
models = addOrgRepoToModels(models)
storeModels(models = models, key = key, testing = testing)