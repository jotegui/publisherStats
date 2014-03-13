#!/usr/bin/python

import logging
import monthlyStatReports
from datetime import datetime

logging.basicConfig(filename='beta.log', format='%(levelname)s:%(asctime)s %(message)s', level=logging.DEBUG)

ini = datetime.now()
logging.info('Initiated at {0}'.format(ini))

stat_reports_path = './statReports2014_03_04.json'

try:
    logging.info('Trying to delete previous reports. Info taken from file {0}'.format(stat_reports_path))
    db.main(stat_reports_path = stat_reports_path, testing = False)
    logging.info('Deletion finished. Check log for result')
except:
    logging.warning('File not found, avoiding deletion.')

monthlyStatReports.main(lapse='month', testing=True)

end = datetime.now()
dif = end - ini

logging.info('elapsed {0}'.format(dif))
logging.info('done')
