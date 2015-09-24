import time
import json
import logging
import requests
from generateReports import get_time_lapse

__author__ = '@jotegui'

issue_reports_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'issueReports_{0}.json')
#empty_issue_reports_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'emptyIssueReports_{0}.json')


#def create_empty_issue(git_url, key, today, testing=False):
#    """Create issue stating there is no data for that resource in that month."""
#    org = git_url['github_orgname']
#    repo = git_url['github_reponame']
#    
#    created = get_time_lapse(today=today)[0]
#    
#    title = 'Monthly VertNet data use report for {0}, resource {1}'.format(created, repo)
#    body = """Unfortunately, there is no usage data for your resource this month. None of the records from this resource appeared in any search or download event during the last month.
#You can find more information on the reporting system here: http://www.vertnet.org/resources/usagereportingguide.html
#Please post any comments or questions to http://www.vertnet.org/feedback/contact.html
#Thank you for being a part of VertNet.
#"""
#    labels = ['report']
#
#    if testing is True:
#        org = 'jotegui'
#        repo = 'statReports'
#
#    headers = {'User-Agent': 'VertNet', 'Authorization': 'token {0}'.format(key)}
#    url = 'https://api.github.com/repos/{0}/{1}/issues'.format(org, repo)
#    data = json.dumps({'title': title, 'body': body, 'labels': labels})
#    r = requests.post(url, headers=headers, data=data)
#
#    status_code = r.status_code
#
#    if status_code == 201:
#        logging.info('SUCCESS - Empty issue created for resource {0}'.format(repo))
#    else:
#        logging.error('EMPTY ISSUE CREATION FAILED for resource {0}'.format(repo))
#
#    return r
    
    
def create_issue(git_url, key, today, testing=False):
    """Create individual issue on repository indicating the new monthly report"""
    org = git_url['org']
    repo = git_url['repo']

    created = get_time_lapse(today=today)[0]

    link_txt = 'https://github.com/{0}/{1}/blob/master/{2}'.format(org, repo, git_url['path_txt'])
    link_html = 'https://github.com/{0}/{1}/blob/master/{2}'.format(org, repo, git_url['path_html'])
    link_pretty_html = 'http://htmlpreview.github.io/?' + link_html

    title = 'Monthly VertNet data use report for {0}, resource {1}'.format(created, repo)
    body = """Your monthly VertNet data use report is ready!
You can see the HTML rendered version of the reports through this link {2} or you can see and download the raw report via GitHub as a text file ({0}) or HTML file ({1}).
To download the report, please log in to your GitHub account and view either the text or html document linked above.  Next, click the "Raw" button to save the page.  You can also right-click on "Raw" and use the "Save link as..." option. The txt file can be opened with any text editor. To correctly view the HTML file, you will need to open it with a web browser.
You can find more information on the reporting system, along with an explanation of each metric, here: http://www.vertnet.org/resources/usagereportingguide.html
Please post any comments or questions to http://www.vertnet.org/feedback/contact.html
Thank you for being a part of VertNet.
""".format(link_txt, link_html, link_pretty_html)
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
    
    time.sleep(5)  # Wait 5 secs to avoid abuse triggers
    return r


def create_issues(git_urls, key, today, testing=False):
    """Iterate over list of repositories to create individual issues for each one"""
    issues = {}
    for git_url in git_urls:
        r = create_issue(git_url=git_urls[git_url], key=key, today=today, testing=testing)
        issues[git_url] = json.loads(r.content)

    return issues


#def create_empty_issues(git_urls, key, today, testing=False):
#    """Iterate over list of empty repositories to create individual issues for each one"""
#    issues = {}
#    for git_url in git_urls:
#        r = create_empty_issue(git_url=git_url, key=key, today=today, testing=testing)
#        issues[git_url] = json.loads(r.content)
#    
#    return issues


#def get_all_repos():
#    """Extract a list of all github repositories."""
#    url = "https://vertnet.cartodb.com/api/v2/sql"
#    query = "select github_orgname, github_reponame from resource_staging where ipt is true and networks like '%VertNet%'"
#    params = {'q':query}
#    r = requests.get(url, params=params)
#    if r.status_code == 200:
#        logging.info("List of all repositories extracted successfully")
#        all_repos = json.loads(r.content)['rows']
#        return all_repos
#    else:
#        logging.error("Something went wrong extracting list of repositories")
#        logging.error(r.text)
#        return None


#def check_empty_repos(git_urls, all_repos):
#    """Extract a list of github repositories for which there is no data this month."""
#    empty_repos = []
#    existing_repos = [{'github_orgname': git_urls[x]['org'], 'github_reponame':git_urls[x]['repo']} for x in git_urls.keys()]
#    for i in all_repos:
#        if i not in existing_repos:
#            empty_repos.append(i)
#    return empty_repos
    

def main(git_urls, key, today, testing=False):
    """Main function for creating and storing monthly stats awareness issues."""

    # Create issues in github
    issues = create_issues(git_urls=git_urls, key=key, today=today, testing=testing)
    
    # Store git data on the generated issues locally
    with open(issue_reports_path.format(format(today, '%Y_%m_%d')), 'w') as g:
        g.write(json.dumps(issues))
    logging.info('GIT ISSUES stored in local file issueReports_{0}.json'.format(format(today, '%Y_%m_%d')))
    
#    # Get all github repos from cartodb
#    all_repos = get_all_repos()
#    
#    # Get resources for which there is no data this month
#    empty_repos = check_empty_repos(git_urls, all_repos)
#    
#    # Create an issue for each empty resource
#    empty_issues = create_empty_issues(empty_repos=empty_repos, key=key, today=today, testing=testing)
#    
#    with open(empty_issue_report_path.format(format(today, '%Y_%m_%d')), 'w') as g:
#        g.write(json.dumps(empty_issues))
#    logging.info('EMPTY GIT ISSUES stored in local file emptyIssueReports_{0}.json'.format(format(today, '%Y_%m_%d')))

    return
