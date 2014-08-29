import checkNameConsistency
import extractStats
import generateReports
import uploadToGithub
import addIssueToGithub
from util import *
import pickle

__author__ = '@jotegui'


def main(today, lapse='month', testing=False, beta=False, local=False, local_file=None, github=True):
    """Main function"""
    
    # Check repository name consistency between CartoDB and GitHub
    checkNameConsistency.main()
    
    # Get API key, depending on whether or not it is in testing mode
    key = apikey(testing=testing)

    # (1) Extract downloads data: extractStats module
    if local is False:
        pubs = extractStats.main(today=today, lapse=lapse, testing=testing)
    else:
        logging.info("Loading from local file {0}".format(local_file))
        with open(local_file, 'rb') as inp_file:
            pubs = pickle.load(inp_file)

    # (2) Generate reports and models: generateReports module
    reports, models = generateReports.main(pubs=pubs, lapse=lapse, today=today)

    if github is True:

        # (3) Put reports and models in GitHub: uploadToGithub module
        git_urls = uploadToGithub.main(reports=reports, models=models, key=key, today=today, testing=testing, beta=beta)

        # (4) Create issues to notify users: addIssueToGithub module
        addIssueToGithub.main(git_urls=git_urls, key=key, today=today, testing=testing)

        return

    else:
        return reports
