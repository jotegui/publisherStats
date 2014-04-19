import time
import base64
import json
import logging
import requests
from util import get_org_repo


def beta_testing(reports, models, beta=False):
    """Store data on betatesters only if in beta mode"""

    if beta is True:
        reports2 = {}
        models2 = {}
        testing_insts = open('./TestingInsts.txt', 'r').read().rstrip().split(' ')
        for pub in reports:
            inst = reports[pub]['inst']
            if inst in testing_insts:
                reports2[pub] = reports[pub]
                models2[pub] = models[pub]
    else:
        reports2 = reports
        models2 = models

    return reports2, models2


def put_all(reports, key, testing=False):
    """Iterate through all reports and store them in GitHub"""
    # Review the iteration to check for errors -- Looks like there's no issue if wait between two PUTs

    git_urls = {}
    pubs_to_check = reports.keys()
    retry = 0

    while len(pubs_to_check) > 0 and retry < 5:

        retry += 1

        for pub in reports:
            if pub in pubs_to_check:
                pubs_to_check.pop(pubs_to_check.index(pub))
                report = reports[pub]
                org, repo = get_org_repo(report['url'])

                # Testing values
                if testing is True:
                    org = 'jotegui'
                    repo = 'statReports'

                path_txt, sha_txt, git_url_txt, path_html, sha_html, git_url_html = put_report(report, pub, org,
                                                                                               repo, key)
                if sha_txt == '' and sha_html != '':
                    logging.warning('File {0} failed to upload, deleting {1}'.format(path_txt, path_html))
                    del_github_file(org, repo, path_html, sha_html, key)
                    pubs_to_check.append(pub)
                elif sha_html == '' and sha_txt != '':
                    pubs_to_check.append(pub)
                    logging.warning('File {0} failed to upload, deleting {1}'.format(path_html, path_txt))
                    del_github_file(org, repo, path_txt, sha_txt, key)
                elif sha_txt == '' and sha_html == '':
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

    logging.info('Finished putting stats in github repos')
    return git_urls


def put_report(report, pub, org, repo, key):
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
    headers = {'User-Agent': 'VertNet', 'Authorization': 'token {0}'.format(key)}
    request_url_txt = 'https://api.github.com/repos/{0}/{1}/contents/{2}'.format(org, repo, path_txt)
    request_url_html = 'https://api.github.com/repos/{0}/{1}/contents/{2}'.format(org, repo, path_html)

    #logging.info('Requesting PUT txt for {0}:{1}:{2}'.format(org, repo, path_txt))
    r = requests.put(request_url_txt, data=json_input_txt, headers=headers)

    status_code = r.status_code
    response_content = json.loads(r.content)

    if status_code == 201:
        logging.info('SUCCESS (Status Code {0}) - SHA: {1}'.format(status_code, response_content['content']['sha']))
        git_url_txt = response_content['content']['git_url']
        sha_txt = response_content['content']['sha']
    else:
        logging.error('PUT {0}:{1}:{2} Failed. Status Code {3}. Message: {4}'.format(org, repo, path_txt, status_code,
                                                                                     response_content['message']))
        git_url_txt = ''
        sha_txt = ''
    time.sleep(2)  # Wait 2 seconds between insert and insert to avoid 409

    #logging.info('Requesting PUT html for {0}:{1}:{2}'.format(org, repo, path_html))
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
    time.sleep(2)  # Wait 2 seconds between insert and insert to avoid 409
    return path_txt, sha_txt, git_url_txt, path_html, sha_html, git_url_html


def put_store_reports(reports, key, today, testing=False):
    """Main process to put all reports in GitHub and store the git_urls locally"""

    # Put all reports in GitHub
    git_urls = put_all(reports=reports, key=key, testing=testing)

    # Store git data on the generated reports locally
    f = open('./statReports_{0}.json'.format(format(today, '%Y_%m_%d')), 'w')
    f.write(json.dumps(git_urls))
    f.close()
    logging.info('GIT URLs stored in local file statReports_{0}.json'.format(format(today, '%Y_%m_%d')))

    return git_urls


def del_github_file(org, repo, path, sha, key):
    """Delete a single report file in GitHub"""
    message = "Deleting file {0}".format(path)
    commiter = {'name': 'VertNet', 'email': 'vertnetinfo@vertnet.org'}
    json_input = json.dumps({'message': message, 'commiter': commiter, 'sha': sha})

    request_url = 'https://api.github.com/repos/{0}/{1}/contents/{2}'.format(org, repo, path)
    headers = {'User-Agent': 'VertNet', 'Authorization': 'token {0}'.format(key)}

    logging.info('Requesting DELETE for {0}:{1}:{2}'.format(org, repo, path))
    r = requests.delete(request_url, data=json_input, headers=headers)

    status_code = r.status_code
    response_content = json.loads(r.content)

    if status_code == 200:
        logging.info(
            'SUCCESS DELETING {2} (Status Code {0}) - COMMIT SHA: {1}'.format(
                status_code, response_content['commit']['sha'], path
            )
        )
    else:
        logging.error('DELETE {0}:{1}:{2} Failed. Status Code {3}. Message: {4}'.format(org, repo, path, status_code,
                                                                                        response_content['message']))
    time.sleep(2)  # Wait 2 seconds between insert and insert to avoid 409
    return


def delete_all(git_urls, key):
    """Iterate through a list of files to delete from GitHub"""
    for pub in git_urls:
        org = git_urls[pub]['org']
        repo = git_urls[pub]['repo']
        path = git_urls[pub]['path_txt']
        sha = git_urls[pub]['sha_txt']
        del_github_file(org, repo, path, sha, key)
        path = git_urls[pub]['path_html']
        sha = git_urls[pub]['sha_html']
        del_github_file(org, repo, path, sha, key)
    logging.info('Finished deleting stats from github repos')
    return


def store_models(models, key, testing=False):

    try:
        model_urls = json.loads(open('./modelURLs.json', 'r').read().rstrip())
    except IOError:
        model_urls = {}

    if testing is True:
        org = 'jotegui'
        repo = 'statReports'
    else:  # TODO: Update this block
        from util import apikey  # Remove when repo changed to VertNet
        key = apikey(True)  # Remove when repo changed to VertNet
        org = 'jotegui'  # Change to VertNet org
        repo = 'statReports'  # Change to VertNet repo

    for model in models:

        #created_at = models[model]['created_at'].replace('/', '_')
        message = 'Putting JSON data on {0} for {1}, {2}'.format(models[model]['report_month'],
                                                                 models[model]['github_org'],
                                                                 models[model]['github_repo'])
        commiter = {'name': 'VertNet', 'email': 'vertnetinfo@vertnet.org'}
        content = base64.b64encode(json.dumps(models[model]))
        path = 'data/{0}_{1}.json'.format(model.replace(' ', '_'), models[model]['report_month'].replace('/', '_'))

        headers = {'User-Agent': 'VertNet', 'Authorization': 'token {0}'.format(key)}
        request_url = 'https://api.github.com/repos/{0}/{1}/contents/{2}'.format(org, repo, path)
        json_input = json.dumps({"message": message, "commiter": commiter, "content": content})

        r = requests.put(request_url, data=json_input, headers=headers)
        status_code = r.status_code

        if status_code == 201:
            logging.info('SUCCESS - Data model stored for resource {0}'.format(repo))
        else:
            logging.error('DATA MODEL CREATION FAILED for resource {0}'.format(repo))
        time.sleep(2)  # Wait 2 sput_store_reportseconds between insert and insert to avoid 409

        if model not in model_urls:
            model_urls[model] = [request_url]
        else:
            model_urls[model].append(request_url)

    # Store urls on the generated models
    f = open('./modelURLs.json', 'w')
    f.write(json.dumps(model_urls))
    f.close()
    logging.info('MODEL URLs stored in local file modelURLs.json')

    return


def main(reports, models, key, today, testing=False, beta=False):
    # Limit to betatesters
    reports, models = beta_testing(reports=reports, models=models, beta=beta)

    # Put all reports in github
    git_urls = put_store_reports(reports=reports, key=key, today=today, testing=testing)

    # Put all models in github
    if testing is False:
        store_models(models=models, key=key, testing=testing)

    return git_urls
