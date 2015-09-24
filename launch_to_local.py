#!/usr/bin/python

import os
import logging
from datetime import datetime
import extractStats
import pickle
import os

__author__ = '@jotegui'

today = datetime.now()

file_name = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'pubs_{0}.pk'.format(format(today, '%Y_%m_%d')))

logging.basicConfig(filename=os.path.join(os.path.abspath(os.path.dirname(__file__)), 'logs', 'to_local_{0}.log'.format(format(today, '%Y_%m_%d'))),
                    format='%(levelname)s:%(asctime)s %(message)s', level=logging.DEBUG)

lapse = 'month'
testing = False
# key = apikey(testing)
# beta = True

pubs = extractStats.main(today=today, lapse=lapse, testing=testing)

# Piece of code to store pubs in disk (to avoid 1h+ of downloads)
logging.info('Writing to local file pubs_{0}.pk'.format(format(today, '%Y_%m_%d')))
with open(file_name, 'wb') as output:
    pickle.dump(pubs, output, pickle.HIGHEST_PROTOCOL)

end = datetime.now()
dif = end - today

logging.info('elapsed {0}'.format(dif))
logging.info('done')
