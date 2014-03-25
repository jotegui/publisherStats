import extractStats
import generateReports
import uploadToGithub
import addIssueToGithub
from util import *
import pickle

__author__ = 'jotegui'


def main(today, lapse='month', testing=False, beta=False, local=False, local_file=None, github=True):
    """Main function"""

    # Get API key
    key = apikey(testing=testing)

    # Extract downloads data
    if local is False:
        pubs = extractStats.main(today=today, lapse=lapse, testing=testing)
    else:
        with open(local_file, 'rb') as inp_file:
            pubs = pickle.load(inp_file)

    # Generate reports and models
    reports, models = generateReports.main(pubs=pubs, lapse=lapse, today=today)

    if github is True:

        # Put reports and models in GitHub
        git_urls = uploadToGithub.main(reports=reports, models=models, key=key, today=today, testing=testing, beta=beta)

        # Create issues to notify users
        addIssueToGithub.main(git_urls=git_urls, key=key, today=today, testing=testing)

        return

    else:
        return reports