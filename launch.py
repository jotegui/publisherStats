#!/usr/bin/python
"""
Script to generate reports of the content of each institution based on the download files.

Run without arguments to generate the stats of the previous month.
Run with "full" argument to generate stats for all available files.

Reports will be created in a new folder called "reports" in the same folder where this script resides.

This file will (hopefully) be part of the VertNet Project (http://www.vertnet.org)
"""

import uploadToGithub as up
from datetime import datetime

ini = datetime.now()

up.main(testing = True)

end = datetime.now()
dif = end - ini

print "elapsed: {0}".format(dif)
print 'done'
