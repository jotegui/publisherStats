#!/usr/bin/python

import logging
import uploadToGithub as up
import deleteBetaReports as db
from datetime import datetime

logging.basicConfig(filename='beta.log', format='%(levelname)s:%(asctime)s %(message)s', level=logging.DEBUG)

ini = datetime.now()
logging.info('Initiated at {0}'.format(ini))

stat_reports_path = './statReports2014_03_04.json'
try:
    logging.info('Trying to delete previous reports. Info taken from file {0}'.format(stat_reports_path))
    db.main(stat_reports_path)
    logging.info('Deletion finished. Check log for result')
except:
    logging.warning('File not found, avoiding deletion.')

up.main(lapse='month', testing=False, beta=True)

end = datetime.now()
dif = end - ini

logging.info('elapsed {0}'.format(dif))
logging.info('done')
