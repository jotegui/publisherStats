from datetime import datetime
import logging
import addIssueToGithub
import extractStats
import generateReports
import uploadToGithub
from util import apikey

__author__ = 'jotegui'

logging.basicConfig(  # filename='logs/future_{0}.log'.format(format(datetime.now(), '%Y_%m_%d')),
    format='%(levelname)s:%(asctime)s %(message)s', level=logging.DEBUG)


# Get Today...
today = datetime.now()
# ... and add 1 month
today = today.replace(month=today.month+1)

testing = True
lapse = 'month'
beta = True

# Extract stats for March
key = apikey(testing=testing)
pubs = extractStats.main(today=today, lapse=lapse, testing=testing)
reports, models = generateReports.main(pubs=pubs, lapse=lapse, today=today)

git_urls = uploadToGithub.main(reports=reports, models=models, key=key, today=today, testing=testing, beta=beta)
addIssueToGithub.main(git_urls=git_urls, key=key, today=today, testing=testing)