import os
import base64
import json
import urllib2
import logging
import requests
import generateReports as gr
from datetime import datetime
from generateReports import getTimeLapse


def apikey():
    """Return credentials file as a JSON object."""
    #keyname = 'api.key'
    keyname = 'JOT.key'
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), keyname)
    key = open(path, "r").read().rstrip()
    return key


def sanityCheck(url):
    """Change some modified URLs to match values in CartoDB"""
    if url == 'http://gbif.rom.on.ca:8180/ipt/resource.do?r=herpetology':
        new_url = 'http://gbif.rom.on.ca:8180/ipt/resource.do?r=herps'
    elif url == 'http://gbif.rom.on.ca:8180/ipt/resource.do?r=birdspasserines':
        new_url = 'http://gbif.rom.on.ca:8180/ipt/resource.do?r=birdspass'
    elif url == 'http://gbif.rom.on.ca:8180/ipt/resource.do?r=mammalogyspecimens':
        new_url = 'http://gbif.rom.on.ca:8180/ipt/resource.do?r=mamm'
    elif url == 'http://gbif.rom.on.ca:8180/ipt/resource.do?r=birdsnonpasserines':
        new_url = 'http://gbif.rom.on.ca:8180/ipt/resource.do?r=birdsnonpass'
    elif url == 'http://gbif.rom.on.ca:8180/ipt/resource.do?r=vertebratepalaeorecentskeletons':
        new_url = 'http://gbif.rom.on.ca:8180/ipt/resource.do?r=vposteology'
    # More to be added as needed
    else:
        new_url = url

    return new_url


#def getOrg(inst):
#    """Extract organization name for given institutioncode"""
#    if inst.upper() == 'MVZOBS':
#        org = 'mvz-vertnet'
#    else:
#        query_url = 'https://vertnet.cartodb.com/api/v2/sql?q=select%20distinct%20github_orgname%20from%20resource_staging%20where%20icode=%27{0}%27'.format(inst)
#        org = json.loads(urllib2.urlopen(query_url).read())['rows'][0]['github_orgname']
#    return org

#def getRepoList(org):
#    """Extract list of available repositories for a given github organization"""
#    repo_list = []
#    query_url = 'https://vertnet.cartodb.com/api/v2/sql?q=select%20github_reponame%20from%20resource_staging%20where%20github_orgname=%27{0}%27'.format(org)
#    d0 = json.loads(urllib2.urlopen(query_url).read())['rows']
#    for i in d0:
#        repo_list.append(i['github_reponame'])
#    return repo_list

def getOrgRepoByURL(url):
    """Extract github organization and repository by datasource url"""
    url = sanityCheck(url)
    query_url = 'https://vertnet.cartodb.com/api/v2/sql?q=select%20github_orgname,%20github_reponame%20from%20resource_staging%20where%20url=%27{0}%27'.format(
        url)
    try:
        d = json.loads(urllib2.urlopen(query_url).read())['rows'][0]
        org = d['github_orgname']
        repo = d['github_reponame']
    except IndexError:
        logging.error('Getting Org and Repo by URL failed with url {0}'.format(url))
        org = None
        repo = None
    return org, repo


#def getOrgRepo(report):
#    
#    inst = report['inst']
#    col = report['col']
#    
#    try:
#        org = getOrg(inst)
#    except IndexError:
#        org = getOrg(col.split('_')[0].upper())
#    
#    repo_list = getRepoList(org)
#    
#    if col.replace('_','-') in repo_list:
#        repo = col.replace('_','-')
#    else:
#        repo = None
#        logging.error('Could not find repository name for Inst {0}, Col {1}'.format(inst, col))
#    
#    return org, repo

def putReportInRepo(report, pub, org, repo):
    """Upload a single report text to a github repository"""

    # Prepare variables
    report_content_txt = report['content_txt']
    report_content_html = report['content_html']
    created_at = report['created_at']
    path_txt = 'reports/{0}_{1}.txt'.format(pub.replace(' ', '_'), created_at)
    path_html = 'reports/{0}_{1}.html'.format(pub.replace(' ', '_'), created_at)
    message = report_content_txt.split("\n")[1]  # Extract date from report
    content_txt = base64.b64encode(report_content_txt)  # Content has to be base64 encoded
    content_html = base64.b64encode(report_content_html)  # Content has to be base64 encoded
    commiter = {'name': 'VertNet', 'email': 'vertnetinfo@vertnet.org'}  # I think API token overrides this
    json_input_txt = json.dumps({"message": message, "commiter": commiter, "content": content_txt})
    json_input_html = json.dumps({"message": message, "commiter": commiter, "content": content_html})

    # Build PUT request
    key = apikey()
    headers = {'User-Agent': 'VertNet', 'Authorization': 'token {0}'.format(key)}
    request_url_txt = 'https://api.github.com/repos/{0}/{1}/contents/{2}'.format(org, repo, path_txt)
    request_url_html = 'https://api.github.com/repos/{0}/{1}/contents/{2}'.format(org, repo, path_html)

    logging.info('Requesting PUT txt for {0}:{1}:{2}'.format(org, repo, path_txt))
    r = requests.put(request_url_txt, data=json_input_txt, headers=headers)

    status_code = r.status_code
    response_content = json.loads(r.content)

    if status_code == 201:
        #logging.info('SUCCESS (Status Code {0}) - SHA: {1}'.format(status_code, response_content['content']['sha']))
        git_url_txt = response_content['content']['git_url']
        sha_txt = response_content['content']['sha']
    else:
        logging.error('PUT {0}:{1}:{2} Failed. Status Code {3}. Message: {4}'.format(org, repo, path_txt, status_code,
                                                                                     response_content['message']))
        git_url_txt = ''
        sha_txt = ''

    logging.info('Requesting PUT html for {0}:{1}:{2}'.format(org, repo, path_html))
    r = requests.put(request_url_html, data=json_input_html, headers=headers)

    status_code = r.status_code
    response_content = json.loads(r.content)

    if status_code == 201:
        #logging.info('SUCCESS (Status Code {0}) - SHA: {1}'.format(status_code, response_content['content']['sha']))
        git_url_html = response_content['content']['git_url']
        sha_html = response_content['content']['sha']
    else:
        logging.error('PUT {0}:{1}:{2} Failed. Status Code {3}. Message: {4}'.format(org, repo, path_html, status_code,
                                                                                     response_content['message']))
        git_url_html = ''
        sha_html = ''

    return path_txt, sha_txt, git_url_txt, path_html, sha_html, git_url_html


def deleteFileInGithub(org, repo, path, sha):
    message = "Deleting file {0}".format(path)
    commiter = {'name': 'VertNet', 'email': 'vertnetinfo@vertnet.org'}
    json_input = json.dumps({'message': message, 'commiter': commiter, 'sha': sha})

    key = apikey()
    request_url = 'https://api.github.com/repos/{0}/{1}/contents/{2}'.format(org, repo, path)
    headers = {'User-Agent': 'VertNet', 'Authorization': 'token {0}'.format(key)}

    logging.info('Requesting DELETE for {0}:{1}:{2}'.format(org, repo, path))
    r = requests.delete(request_url, data=json_input, headers=headers)

    status_code = r.status_code
    response_content = json.loads(r.content)

    if status_code == 200:
        logging.info(
            'SUCCESS (Status Code {0}) - COMMIT SHA: {1}'.format(status_code, response_content['commit']['sha']))
    else:
        logging.error('DELETE {0}:{1}:{2} Failed. Status Code {3}. Message: {4}'.format(org, repo, path, status_code,
                                                                                        response_content['message']))
    return


def deleteAll(git_urls):
    for pub in git_urls:
        org = git_urls[pub]['org']
        repo = git_urls[pub]['repo']
        path = git_urls[pub]['path_txt']
        sha = git_urls[pub]['sha_txt']
        deleteFileInGithub(org, repo, path, sha)
        path = git_urls[pub]['path_html']
        sha = git_urls[pub]['sha_html']
        deleteFileInGithub(org, repo, path, sha)
    logging.info('Finished deleting stats from github repos')
    return


def putAll(reports, testing):
    git_urls = {}

    pubs_to_check = reports.keys()
    retry = 0

    while len(pubs_to_check) > 0 and retry < 5:

        retry += 1
        errors = False
        #pubs_to_check = []

        for pub in reports:
            if pub in pubs_to_check:
                pubs_to_check.pop(pubs_to_check.index(pub))
                report = reports[pub]
                org, repo = getOrgRepoByURL(report['url'])

                # Testing values
                if testing is True:
                    org = 'jotegui'
                    repo = 'statReports'

                path_txt, sha_txt, git_url_txt, path_html, sha_html, git_url_html = putReportInRepo(report, pub, org,
                                                                                                    repo)

                if sha_txt == '' and sha_html != '':
                    errors = True
                    logging.warning('File {0} failed to upload, deleting {1}'.format(path_txt, path_html))
                    deleteFileInGithub(org, repo, path_html, sha_html)
                    pubs_to_check.append(pub)
                elif sha_html == '' and sha_txt != '':
                    errors = True
                    pubs_to_check.append(pub)
                    logging.warning('File {0} failed to upload, deleting {1}'.format(path_html, path_txt))
                    deleteFileInGithub(org, repo, path_txt, sha_txt)
                elif sha_txt == '' and sha_html == '':
                    errors = True
                    logging.warning('Both files {0} and {1} failed to upload, deleting'.format(path_txt, path_html))
                    pubs_to_check.append(pub)
                else:
                    git_urls[pub] = {
                        'org': org,
                        'repo': repo,
                        'path_txt': path_txt,
                        'sha_txt': sha_txt,
                        'git_url_txt': git_url_txt,
                        'path_html': path_html,
                        'sha_html': sha_html,
                        'git_url_html': git_url_html
                    }
                    #if error is False:
                    #    break
    logging.info('Finished putting stats in github repos')
    return git_urls


def createIssue(git_url, testing=False):
    org = git_url['org']
    repo = git_url['repo']

    created = getTimeLapse()

    link_txt = 'https://github.com/{0}/{1}/blob/master/{2}'.format(org, repo, git_url['path_txt'])
    link_html = 'https://github.com/{0}/{1}/blob/master/{2}'.format(org, repo, git_url['path_html'])
    link_pretty_html = 'http://htmlpreview.github.io/?' + link_html

    title = 'Monthly VertNet data use report {0}, resource {1}'.format(created, repo)
    body = ("Your monthly VertNet data use report is ready!\n"
            "\n"
            "You can see and download the report in GitHub as a raw text file ({0}) or as a raw HTML file ({1}), or you can see the rendered HTML version of the report through this link: {2}.\n"
            "\n"
            "To download the report, please log in to your GitHub account and view either the text or html document linked above.  Next, click the \"Raw\" button to save the page.  You can also right-click on \"Raw\" and use the \"Save link as...\" option. The txt file can be opened with any text editor. To correctly view the HTML file, you will need to open it with a web browser.\n"
            "\n"
            "Please post any comments or questions to http://www.vertnet.org/feedback/contact.html.\n"
            "\n"
            "Thank you for being a part of VertNet."
    ).format(link_txt, link_html, link_pretty_html)
    labels = ['report']

    if testing is True:
        org = 'jotegui'
        repo = 'statReports'

    key = apikey()
    headers = {'User-Agent': 'VertNet', 'Authorization': 'token {0}'.format(key)}
    url = 'https://api.github.com/repos/{0}/{1}/issues'.format(org, repo)
    data = json.dumps({'title': title, 'body': body, 'labels': labels})
    r = requests.post(url, headers=headers, data=data)

    status_code = r.status_code
    response_content = json.loads(r.content)

    if status_code == 201:
        logging.info('SUCCESS - Issue created for resource {0}'.format(repo))
    else:
        logging.error('ISSUE CREATION FAILED for resource {0}'.format(repo))

    return r


def createIssues(git_urls, testing=False):
    issues = {}
    for git_url in git_urls:
        r = createIssue(git_urls[git_url], testing)
        issues[git_url] = json.loads(r.content)

    return issues


def storeModels(models, testing=False):

    if testing is True:
        org = 'jotegui'
        repo = 'statReports'
    else:
        org = 'jotegui'
        repo = 'statReports'

    for model in models:
        created_at = models[model]['created_at'].replace('/', '_')
        message = 'Putting JSON data on {0} for {1}, {2}'.format(models[model]['report_month'], models[model]['github_org'], models[model]['github_repo'])
        commiter = {'name': 'VertNet', 'email': 'vertnetinfo@vertnet.org'}
        content = base64.b64encode(json.dumps(models[model]))
        path = 'data/{0}_{1}.json'.format(model.replace(' ', '_'), created_at)

        key = apikey()
        headers = {'User-Agent': 'VertNet', 'Authorization': 'token {0}'.format(key)}
        request_url = 'https://api.github.com/repos/{0}/{1}/contents/{2}'.format(org, repo, path)
        json_input = json.dumps({"message": message, "commiter": commiter, "content": content})

        r = requests.put(request_url, data=json_input, headers=headers)
        status_code = r.status_code
        response_content = json.loads(r.content)

        if status_code == 201:
            logging.info('SUCCESS - Data model stored for resource {0}'.format(repo))
        else:
            logging.error('DATA MODEL CREATION FAILED for resource {0}'.format(repo))
    return


def main(lapse='month', testing=False, beta=False, local=False):
    if local is False:
        reports, models = gr.main(lapse=lapse, testing=testing)
    else:
        reports = {}
        reports_folder = 'reports2014_03_05'
        files = os.listdir('./{0}/'.format(reports_folder))
        for i in files:
            d = json.loads(open('./{0}/{1}'.format(reports_folder, i), 'r').read().rstrip())
            pub = '{0}-{1}'.format(d['inst'], d['col'].replace('_', '-'))
            reports[pub] = d

    if beta is True:
        reports2 = {}
        models2 = {}
        testingInsts = open('./TestingInsts.txt', 'r').read().rstrip().split(' ')
        for pub in reports:
            inst = reports[pub]['inst']
            if inst in testingInsts:
                reports2[pub] = reports[pub]
                models2[pub] = models[pub]
    else:
        reports2 = reports
        models2 = models

    # Add org and repo to models
    for i in models2:
        org, repo = getOrgRepoByURL(models2[i]['url'])
        models2[i]['github_org'] = org
        models2[i]['github_repo'] = repo

    # Put all reports in github
    git_urls = putAll(reports=reports2, testing=testing)

    # Store git data on the generated reports locally
    f = open('./statReports_{0}.json'.format(format(datetime.now(), '%Y_%m_%d')), 'w')
    f.write(json.dumps(git_urls))
    f.close()
    logging.info('GIT URLs stored in local file')

    # Create issues in github
    issues = createIssues(git_urls=git_urls, testing=testing)

    # Store git data on the generated issues locally
    g = open('./issueReports{0}.json'.format(format(datetime.now(), '%Y_%m_%d')), 'w')
    g.write(json.dumps(issues))
    g.close()
    logging.info('GIT ISSUES stored in local file')

    # Put all models in github
    storeModels(models=models2, testing=testing)

    #if testing is True and beta is False:
    #    deleteAll(git_urls)

    return
