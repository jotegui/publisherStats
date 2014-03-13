#!/usr/bin/python

import logging
import monthlyStatReports
from datetime import datetime

logging.basicConfig(filename='logs/test_{0}.log'.format(format(datetime.now(), '%Y_%m_%d')), format='%(levelname)s:%(asctime)s %(message)s', level=logging.DEBUG)

ini = datetime.now()
logging.info('Initiated at {0}'.format(ini))

monthlyStatReports.main(lapse='month', testing=True)

end = datetime.now()
dif = end - ini

logging.info('elapsed: {0}'.format(dif))
logging.info('done')
