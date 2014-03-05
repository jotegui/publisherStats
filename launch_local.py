#!/usr/bin/python

import generateReports as gr
from datetime import datetime

import logging
logging.basicConfig(filename='local.log', format='%(levelname)s:%(asctime)s %(message)s', level=logging.DEBUG)

ini = datetime.now()
logging.info('Initiated at {0}'.format(ini))

gr.main(lapse = 'month', testing = False, local = True)

end = datetime.now()
dif = end - ini

logging.info("elapsed {0}".format(dif))
logging.info('done')
