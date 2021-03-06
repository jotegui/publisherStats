#!/usr/bin/python

import logging
import monthlyStatReports
from datetime import datetime

__author__ = '@jotegui'

ini = datetime.now()

logging.basicConfig(filename='logs/test_{0}.log'.format(format(ini, '%Y_%m_%d')),
                    format='%(levelname)s:%(asctime)s %(message)s', level=logging.DEBUG)


logging.info('Initiated at {0}'.format(ini))

monthlyStatReports.main(today=ini, lapse='month', testing=True, beta=True, github=True)

end = datetime.now()
dif = end - ini

logging.info('elapsed {0}'.format(dif))
logging.info('done')
