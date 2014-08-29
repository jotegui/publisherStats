import requests
import json
import logging

from util import apikey

__author__ = '@jotegui'


ghb_url = 'https://api.github.com'
cdb_url = "https://vertnet.cartodb.com/api/v2/sql"
testing = False
key = apikey(testing)
headers = {
    'User-Agent': 'VertNet',  # Authenticate as VertNet
    'Accept': 'application/vnd.github.v3+json',  # Require version 3 of the API (for stability)
    'Authorization': 'token {0}'.format(key)  # Provide the API key
}


class ConsistencyError(Exception):
	def __init__(self,value):
		self.value=value
	def __str__(self):
		return repr(self.value)


def get_all_repos():
    """Extract a list of all github_orgnames and github_reponames from CartoDB."""
    query = "select github_orgname, github_reponame from resource_staging where ipt is true and networks like '%VertNet%';"
    params = {'q':query}
    r = requests.get(cdb_url, params=params)
    if r.status_code == 200:
        all_repos = json.loads(r.content)['rows']
        return all_repos
    else:
        logging.error("Something went wrong querying CartoDB:")
        logging.error("Status Code:", r.status_code)
        logging.error("Response:", r.text)
        return None


def list_org(org):
    """Get a list of the repositories associated with an organization in GitHub."""
    req_url = '/'.join([ghb_url, 'orgs', org, 'repos'])
    r = requests.get(req_url, headers=headers)
    if r.status_code == 200:
        content = json.loads(r.content)
        return [x['name'] for x in content]
    else:
        return None


def check_failed_repos():
    """Check repository name consistency between CartoDB and GitHub."""
    failed_repos = []
    all_repos = get_all_repos()
    
    for repo in all_repos:
        orgname = repo['github_orgname']
        reponame = repo['github_reponame']
        
        if orgname is None or reponame is None:
            failed_repos.append(repo)
            continue
        
        repo_list = list_org(orgname)

        if repo_list is not None:
            if reponame not in repo_list:
                failed_repos.append(repo)
        else:
            failed_repos.append(repo)
    
    return failed_repos


def main():
    """Main process."""
    logging.info("Checking consistency of repository names between CartoDB and GitHub.")
    failed_repos = check_failed_repos()
    if len(failed_repos) > 0:
        logging.error("There were issues in the repository name matching.")
        for i in failed_repos:
            logging.error("Orgname: {0}, Reponame: {1}".format(i['github_orgname'], i['github_reponame']))
        logging.error("Please fix them and re-launch.")
        raise ConsistencyError("Repository name consistency check failed. See logs.")
    else:
        logging.info("The consistency check could not find any issue. The script can continue.")
        return

if __name__ == "__main__":
    
    main()
