#!/usr/bin/python

import uploadToGithub as up
from datetime import datetime

ini = datetime.now()

up.main(lapse = 'month', testing = False)

end = datetime.now()
dif = end - ini

print "elapsed: {0}".format(dif)
print 'done'
