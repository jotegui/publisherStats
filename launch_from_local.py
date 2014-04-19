#!/usr/bin/python

import logging
import monthlyStatReports
from datetime import datetime

ini = datetime.now()

logging.basicConfig(filename='logs/local_{0}.log'.format(format(ini, '%Y_%m_%d')),
                    format='%(levelname)s:%(asctime)s %(message)s', level=logging.DEBUG)


logging.info('Initiated at {0}'.format(ini))

monthlyStatReports.main(today=ini, lapse='month', testing=True, beta=True, local=True, local_file='pubs_2014_02_b.pk')

end = datetime.now()
dif = end - ini

logging.info('elapsed {0}'.format(dif))
logging.info('done')