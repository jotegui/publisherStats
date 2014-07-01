#!/usr/bin/python

import logging
import monthlyStatReports
from datetime import datetime

ini = datetime.now()

logging.basicConfig(filename='logs/local_{0}.log'.format(format(ini, '%Y_%m_%d')),
                    format='%(levelname)s:%(asctime)s %(message)s', level=logging.DEBUG)


logging.info('Initiated at {0}'.format(ini))

monthlyStatReports.main(today=ini, lapse='month', testing=False, beta=False, local=True, local_file='pubs_2014_06_02.pk')

end = datetime.now()
dif = end - ini

logging.info('elapsed {0}'.format(dif))
logging.info('done')
