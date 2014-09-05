#!/usr/bin/python

import logging
import monthlyStatReports
from datetime import datetime

__author__ = '@jotegui'

file_name = '/home/jotegui/VertNet/PublisherStats/pubs_2014_09_02.pk'

y, m, d = file_name[:-3].split("_")[1:4]
ini = datetime(int(y), int(m), int(d))

# ini = datetime.today()

logging.basicConfig(filename='/home/jotegui/VertNet/PublisherStats/logs/local_{0}.log'.format(format(ini, '%Y_%m_%d')),
                    format='%(levelname)s:%(asctime)s %(message)s', level=logging.DEBUG)


logging.info('Initiated at {0}'.format(ini))

monthlyStatReports.main(today=ini, lapse='month', testing=False, beta=False, local=True, local_file=file_name)

end = datetime.now()
dif = end - ini

logging.info('elapsed {0}'.format(dif))
logging.info('done')
