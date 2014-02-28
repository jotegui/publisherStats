import os
import base64
import json
import urllib2
import requests
import generateReports as gr

def apikey(filename):
    """Return credentials file as a JSON object."""
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), filename)
    key = open(path, "r").read().rstrip()
    return key

def getOrg(icode):
    """Extract organization name for given institutioncode"""
    if icode == 'MVZOBS':
        org = 'mvz-vertnet'
    else:
        query_url = 'https://vertnet.cartodb.com/api/v2/sql?q=select%20distinct%20github_orgname%20from%20resource_staging%20where%20icode=%27{0}%27'.format(icode)
        org = json.loads(urllib2.urlopen(query_url).read())['rows'][0]['github_orgname']
    return org
    
def getRepoList(org):
    """Extract list of available repositories for a given github organization"""
    repo_list = []
    query_url = 'https://vertnet.cartodb.com/api/v2/sql?q=select%20github_reponame%20from%20resource_staging%20where%20github_orgname=%27{0}%27'.format(org)
    d0 = json.loads(urllib2.urlopen(query_url).read())['rows']
    for i in d0:
        repo_list.append(i['github_reponame'])
    return repo_list

def getOrgRepo(report):
    
    inst = report['inst']
    col = report['col']
    
    try:
        org = getOrg(inst)
    except IndexError:
        org = getOrg(col.split('_')[0].upper())
    
    repo_list = getRepoList(org)
    
    if col.replace('_','-') in repo_list:
        repo = col.replace('_','-')
    else:
        repo = None
        print 'Could not find repository name for Inst {0}, Col {1}'.format(inst, col)
    
    return org, repo
    
def putReportInRepo(report, pub, org, repo, testing):
    """Upload a single report text to a github repository"""
    
    # Prepare variables
    report_content_txt = report['content_txt']
    report_content_html = report['content_html']
    created_at = report['created_at']
    #path = 'reports/{0}_{1}.txt'.format(repo, created_at)
    path_txt = 'reports/{0}_{1}.txt'.format(pub.replace(' ','_'), created_at)
    path_html = 'reports/{0}_{1}.html'.format(pub.replace(' ','_'), created_at)
    message = report_content_txt.split("\n")[1] # Extract date from report
    content_txt = base64.b64encode(report_content_txt) # Content has to be base64 encoded
    content_html = base64.b64encode(report_content_html) # Content has to be base64 encoded
    commiter = {'name':'VertNet', 'email':'vertnetinfo@vertnet.org'} # I think API token overrides this
    json_input_txt = json.dumps({"message":message, "commiter":commiter, "content":content_txt})
    json_input_html = json.dumps({"message":message, "commiter":commiter, "content":content_html})
    
    # Build PUT request
    if testing is True:
        keyname = 'JOT.key'
    else:
        keyname = 'VN.key'
    key = apikey(keyname)
    headers = {'User-Agent':'VertNet', 'Authorization': 'token {0}'.format(key)}
    request_url_txt = 'https://api.github.com/repos/{0}/{1}/contents/{2}'.format(org, repo, path_txt)
    request_url_html = 'https://api.github.com/repos/{0}/{1}/contents/{2}'.format(org, repo, path_html)
    
    print 'Requesting PUT txt for {0}:{1}:{2}'.format(org, repo, path_txt)
    r = requests.put(request_url_txt, data=json_input_txt, headers=headers)
    
    status_code = r.status_code
    response_content = json.loads(r.content)
    
    if status_code == 201:
        print 'SUCCESS (Status Code {0}) - SHA: {1}'.format(status_code, response_content['content']['sha'])
        git_url_txt = response_content['content']['git_url']
        sha_txt = response_content['content']['sha']
    else:
        print 'ERROR: Status Code {0}. Message: {1}'.format(status_code, response_content['message'])
        git_url_txt = ''
        sha_txt = ''
    
    print 'Requesting PUT html for {0}:{1}:{2}'.format(org, repo, path_html)
    r = requests.put(request_url_html, data=json_input_html, headers=headers)
    
    status_code = r.status_code
    response_content = json.loads(r.content)
    
    if status_code == 201:
        print 'SUCCESS (Status Code {0}) - SHA: {1}'.format(status_code, response_content['content']['sha'])
        git_url_html = response_content['content']['git_url']
        sha_html = response_content['content']['sha']
    else:
        print 'ERROR: Status Code {0}. Message: {1}'.format(status_code, response_content['message'])
        git_url_html = ''
        sha_html = ''
    
    return path_txt, sha_txt, git_url_txt, path_html, sha_html, git_url_html

def deleteFileInGithub(org, repo, path, sha):
    
    message = "Deleting file {0}".format(path)
    commiter = {'name':'VertNet', 'email':'vertnetinfo@vertnet.org'}
    json_input = json.dumps({'message':message, 'commiter':commiter, 'sha':sha})
    
    key = apikey()
    request_url = 'https://api.github.com/repos/{0}/{1}/contents/{2}'.format(org, repo, path)
    headers = {'User-Agent':'VertNet', 'Authorization': 'token {0}'.format(key)}
    
    r = requests.delete(request_url, data=json_input, headers=headers)
    
    status_code = r.status_code
    response_content = json.loads(r.content)
    
    if status_code == 200:
        print 'SUCCESS (Status Code {0}) - COMMIT SHA: {1}'.format(status_code, response_content['commit']['sha'])
    else:
        print 'ERROR: Status Code {0}. Message: {1}'.format(status_code, response_content['message'])
    
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
    print 'Finished deleting stats from github repos'
    return

def putAll(reports, testing):
    git_urls = {}
    
    pubs_to_check = reports.keys()
    retry = 0
    
    while len(pubs_to_check) > 0 and retry < 3:
        
        retry += 1
        error = False
        #pubs_to_check = []
        
        for pub in reports:
            if pub in pubs_to_check:
                pubs_to_check.pop(pubs_to_check.index(pub))
                report = reports[pub]
                org, repo = getOrgRepo(report)
                
                # Testing values
                if testing is True:
                    org = 'jotegui'
                    repo = 'statReports'
                
                path_txt, sha_txt, git_url_txt, path_html, sha_html, git_url_html = putReportInRepo(report, pub, org, repo, testing)
                
                if sha_txt == '' and sha_html != '':
                    errors = True
                    deleteFileInGithub(org, repo, path_txt, sha_txt)
                    pubs_to_check.append(pub)
                elif sha_html == '' and sha_txt != '':
                    errors = True
                    pubs_to_check.append(pub)
                    deleteFileInGithub(org, repo, path_html, sha_html)
                elif sha_txt == '' and sha_html == '':
                    errors = True
                    pubs_to_check.append(pub)
                else:
                    git_urls[pub] = {
                                      'org':org,
                                      'repo':repo,
                                      'path_txt':path_txt,
                                      'sha_txt':sha_txt,
                                      'git_url_txt':git_url_txt,
                                      'path_html':path_html,
                                      'sha_html':sha_html,
                                      'git_url_html':git_url_html
                                    }
    print 'Finished putting stats in github repos'
    return git_urls

def main(lapse = 'full', testing = False):
        
    reports = gr.main(lapse = lapse, testing = testing)
    
    git_urls = putAll(reports = reports, testing = testing)
    
    #if testing is True:
    #    deleteAll(git_urls)
    
    return
