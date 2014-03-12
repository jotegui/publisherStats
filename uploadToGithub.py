import os
import base64
import json
import urllib2
import logging
import requests
import generateReports as gr
from datetime import datetime


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
    url = sanityCheck(url)
    """Extract github organization and repository by datasource url"""
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
                print report['url'], org, repo

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

    git_urls = putAll(reports=reports2, testing=testing)

    # Store monthly values locally (or maybe not?)

    # Store git data on the generated reports locally
    f = open('./statReports_{0}.json'.format(format(datetime.now(), '%Y_%m_%d')), 'w')
    f.write(json.dumps(git_urls))
    f.close()
    logging.info('GIT URLs stored in local file')

    #if testing is True and beta is False:
    #    deleteAll(git_urls)

    return
