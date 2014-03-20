import json
import logging
import requests
from generateReports import getTimeLapse

__author__ = 'jotegui'


def createIssue(git_url, key, today, testing=False):
    """Create individual issue on repository indicating the new monthly report"""
    org = git_url['org']
    repo = git_url['repo']

    created = getTimeLapse(today=today)[0]

    link_txt = 'https://github.com/{0}/{1}/blob/master/{2}'.format(org, repo, git_url['path_txt'])
    link_html = 'https://github.com/{0}/{1}/blob/master/{2}'.format(org, repo, git_url['path_html'])
    link_pretty_html = 'http://htmlpreview.github.io/?' + link_html

    title = 'Monthly VertNet data use report for {0}, resource {1}'.format(created, repo)
    body = ("Your monthly VertNet data use report is ready!\n"
            "\n"
            "You can see and download the report in GitHub as a raw text file ({0}) or as a raw HTML file ({1}), or you can see the rendered HTML version of the report through this link: {2}.\n"
            "\n"
            "To download the report, please log in to your GitHub account and view either the text or html document linked above.  Next, click the \"Raw\" button to save the page.  You can also right-click on \"Raw\" and use the \"Save link as...\" option. The txt file can be opened with any text editor. To correctly view the HTML file, you will need to open it with a web browser.\n"
            "\n"
            "Please post any comments or questions to http://www.vertnet.org/feedback/contact.html.\n"
            "\n"
            "Thank you for being a part of VertNet.\n"
            "\n"
            "IMPORTANT NOTICE: The report generating system is currently in beta. You will likely receive more than one report for this month. This message will no longer appear when we leave the beta status. Thanks for your patience."
    ).format(link_txt, link_html, link_pretty_html)
    labels = ['report']

    if testing is True:
        org = 'jotegui'
        repo = 'statReports'

    headers = {'User-Agent': 'VertNet', 'Authorization': 'token {0}'.format(key)}
    url = 'https://api.github.com/repos/{0}/{1}/issues'.format(org, repo)
    data = json.dumps({'title': title, 'body': body, 'labels': labels})
    r = requests.post(url, headers=headers, data=data)

    status_code = r.status_code

    if status_code == 201:
        logging.info('SUCCESS - Issue created for resource {0}'.format(repo))
    else:
        logging.error('ISSUE CREATION FAILED for resource {0}'.format(repo))

    return r


def createIssues(git_urls, key, today, testing=False):
    """Iterate over list of repositories to create individual issues for each one"""
    issues = {}
    for git_url in git_urls:
        r = createIssue(git_url=git_urls[git_url], key=key, today=today, testing=testing)
        issues[git_url] = json.loads(r.content)

    return issues


def main(git_urls, key, today, testing=False):
    """Main function fro creating and storing monthly stats awareness issues"""

    # Create issues in github
    issues = createIssues(git_urls=git_urls, key=key, today=today, testing=testing)

    # Store git data on the generated issues locally
    g = open('./issueReports_{0}.json'.format(format(today, '%Y_%m_%d')), 'w')
    g.write(json.dumps(issues))
    g.close()
    logging.info('GIT ISSUES stored in local file issueReports_{0}.json'.format(format(today, '%Y_%m_%d')))

    return