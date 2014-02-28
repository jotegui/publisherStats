import os
import base64
import json
import urllib2
import requests
import generateReports as gr

def apikey():
    """Return credentials file as a JSON object."""
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'api.key')
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
    
def putReportInRepo(report, pub, org, repo):
    """Upload a single report text to a github repository"""
    
    # Prepare variables
    report_content = report['content']
    created_at = report['created_at']
    #path = 'reports/{0}_{1}.txt'.format(repo, created_at)
    path = 'reports/{0}_{1}.txt'.format(pub.replace(' ','_'), created_at)
    message = report_content.split("\n")[1] # Extract date from report
    content = base64.b64encode(report_content) # Content has to be base64 encoded
    commiter = {'name':'VertNet', 'email':'vertnetinfo@vertnet.org'} # I think API token overrides this
    json_input = json.dumps({"message":message, "commiter":commiter, "content":content})
    
    # Build PUT request
    key = apikey()
    request_url = 'https://api.github.com/repos/{0}/{1}/contents/{2}'.format(org, repo, path)
    headers = {'User-Agent':'VertNet', 'Authorization': 'token {0}'.format(key)}
    
    print 'Requesting PUT for {0}:{1}'.format(org, repo)
    r = requests.put(request_url, data=json_input, headers=headers)
    
    status_code = r.status_code
    response_content = json.loads(r.content)
    
    if status_code == 201:
        print 'SUCCESS (Status Code {0}) - SHA: {1}'.format(status_code, response_content['content']['sha'])
        git_url = response_content['content']['git_url']
        sha = response_content['content']['sha']
    else:
        print 'ERROR: Status Code {0}. Message: {1}'.format(status_code, response_content['message'])
        git_url = ''
        sha = ''
    
    return path, sha, git_url

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

def main(lapse = 'full', testing = False):
        
    reports = gr.main(lapse = lapse, testing = testing)
    
    git_urls = {}
    
    pubs_to_check = reports.keys()
    retry = 0
    
    while len(pubs_to_check) > 0 and retry < 3:
        
        retry += 1
        error = False
        pubs_to_check = []
        
        for pub in reports:
            report = reports[pub]
            org, repo = getOrgRepo(report)
            
            # Testing values
            if testing is True:
                org = 'jotegui'
                repo = 'statReports'
            
            path, sha, git_url = putReportInRepo(report, pub, org, repo)
            
            if sha == '':
                errors = True
                pubs_to_check.append(pub)
                
            else:
                git_urls[pub] = {
                                  'org':org,
                                  'repo':repo,
                                  'path':path,
                                  'sha':sha,
                                  'git_url':git_url
                                }
        print 'Finished putting stats in github repos'
        
    if testing is True:
        for pub in git_urls:
            org = git_urls[pub]['org']
            repo = git_urls[pub]['repo']
            path = git_urls[pub]['path']
            sha = git_urls[pub]['sha']
            deleteFileInGithub(org, repo, path, sha)
        print 'Finished deleting stats from github repos'
    return
