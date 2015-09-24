#!/usr/bin/python

import logging
from datetime import datetime
import pickle
import extractStats
import monthlyStatReports

__author__ = '@jotegui'

today = datetime.now()

file_name = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'pubs_{0}.pk'.format(format(today, '%Y_%m_%d')))

logging.basicConfig(filename=os.path.join(os.path.abspath(os.path.dirname(__file__)),'logs', 'with_local_{0}.log'.format(format(today, '%Y_%m_%d'))),
                    format='%(levelname)s:%(asctime)s %(message)s', level=logging.DEBUG)

lapse = 'month'
testing = False
beta = False

pubs = extractStats.main(today=today, lapse=lapse, testing=testing)

# Piece of code to store pubs in disk (to avoid 1h+ of downloads)
logging.info('Writing to local file {0}'.format(file_name))
with open(file_name, 'wb') as output:
    pickle.dump(pubs, output, pickle.HIGHEST_PROTOCOL)

# After saving output, continue
monthlyStatReports.main(today=today, lapse=lapse, testing=testing, beta=beta, local=True, local_file=file_name)

end = datetime.now()
dif = end - today

logging.info('elapsed {0}'.format(dif))
logging.info('done')

