#!/usr/bin/python

import uploadToGithub as up
from datetime import datetime

import logging
logging.basicConfig(filename='test.log', format='%(levelname)s:%(asctime)s %(message)s', level=logging.DEBUG)

ini = datetime.now()
logging.info('Initiated at {0}'.format(ini))

up.main(lapse = 'month', testing = True)

end = datetime.now()
dif = end - ini

logging.info("elapsed: {0}".format(dif))
logging.info('done')
