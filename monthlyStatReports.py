import os
import extractStats
import generateReports
import uploadToGithub
import addIssueToGithub

__author__ = 'jotegui'

def apikey(testing):
    """Return credentials file as a JSON object."""
    if testing is False:
        keyname = 'api.key'
    else:
        keyname = 'JOT.key'
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), keyname)
    key = open(path, "r").read().rstrip()
    return key


def main(lapse='month', testing=False, beta=False, local=False, local_folder = None):
    """Main function"""
    # TODO: Implement reading from local files
#    if local is False:
#        reports, models = gr.main(lapse=lapse, testing=testing)
#    else:
#        reports = {}
#        reports_folder = local_folder
#        files = os.listdir('./{0}/'.format(reports_folder))
#        for i in files:
#            d = json.loads(open('./{0}/{1}'.format(reports_folder, i), 'r').read().rstrip())
#            pub = '{0}-{1}'.format(d['inst'], d['col'].replace('_', '-'))
#            reports[pub] = d

    # Get API key
    key = apikey(testing=testing)

    # Extract downloads data
    pubs = extractStats.main(lapse = lapse, testing = testing)

    # Generate reports and models
    reports, models = generateReports.main(pubs, lapse)

    # Put reports and models in GitHub
    git_urls = uploadToGithub.main(reports=reports, models=models, key = key, testing=testing, beta=beta)

    # Create issues to notify users
    addIssueToGithub.main(git_urls = git_urls, key=key, testing = testing)

    return

