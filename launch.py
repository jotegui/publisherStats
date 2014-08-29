#!/usr/bin/python

__author__ = '@jotegui'

import logging
import monthlyStatReports
from datetime import datetime

# Get start time
ini = datetime.now()

# Configure logging
logging.basicConfig(filename='logs/statReports_{0}.log'.format(format(ini, '%Y_%m_%d')),
                    format='%(levelname)s:%(asctime)s %(message)s', level=logging.DEBUG)


logging.info('Initiated at {0}'.format(ini))

# Configure run variables
lapse = 'month'  # Monthly usage ('month') or complete usage ('full')?
testing = False  # Testing? If True, all reports and issues will go to the testing repository
beta = False  # Beta-testing? If True, limit to beta-tester institutions, found in TestingInsts.txt

# Launch main process, no testing and no beta-testers
monthlyStatReports.main(today=ini, lapse=lapse, testing=testing, beta=beta)

# Calculate elapsed time
end = datetime.now()
dif = end - ini
logging.info('elapsed {0}'.format(dif))

# The end
logging.info('done')
