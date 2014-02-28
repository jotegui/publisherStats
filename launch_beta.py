#!/usr/bin/python

import uploadToGithub as up
from datetime import datetime

ini = datetime.now()

up.main(lapse = 'full', testing = True, beta = True)

end = datetime.now()
dif = end - ini

print "elapsed: {0}".format(dif)
print 'done'
