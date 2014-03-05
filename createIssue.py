import json
import requests
from generateReports import getTimeLapse
from uploadToGithub import apikey

def createIssue(git_url):
    org = git_url['org']
    repo = git_url['repo']
    
    #org = 'jotegui'
    #repo = 'statReports'
    
    created = getTimeLapse()
    
    link_txt = 'https://github.com/{0}/{1}/blob/master/{2}'.format(org, repo, git_url['path_txt'])
    link_html = 'https://github.com/{0}/{1}/blob/master/{2}'.format(org, repo, git_url['path_html'])
    link_pretty_html = 'http://htmlpreview.github.io/?'+link_html
    
    title = 'Monthly VertNet data use report {0}, resource {1}'.format(created, repo)
    body = 'Your monthly VertNet data use report is ready!\n\nYou can see and download the report in GitHub as a raw text file ({0}) or as a raw HTML file ({1}), or you can see the rendered HTML version of the report through this link: {2}.\n\nTo download the report, please log in to your GitHub account and view either the text or html document linked above.  Next, click the "Raw" button to save the page.  You can also right-click on "Raw" and use the "Save link as..." option. The txt file can be opened with any text editor. To correctly view the HTML file, you will need to open it with a web browser.\n\nPlease post any comments or questions to http://www.vertnet.org/feedback/contact.html.\n\nThank you for being a part of VertNet.'.format(link_txt, link_html, link_pretty_html)
    labels = ['report']
    
    key = apikey()
    headers = {'User-Agent':'VertNet', 'Authorization': 'token {0}'.format(key)}
    url = 'https://api.github.com/repos/{0}/{1}/issues'.format(org, repo)
    data = json.dumps({'title':title, 'body':body, 'labels':labels})
    r = requests.post(url, headers=headers, data=data)
    
    return r

if __name__ == "__main__":
    raw = json.loads(open('./statReports2014_03_04.json','r').read().rstrip())
    issues = {}
    for d in raw.keys():
        r = createIssue(raw[d])
        issues[d] = json.loads(r.content)
    
    f = open('./issueReports{0}.json'.format(format(datetime.now(), '%Y_%m_%d')),'w')
    f.write(json.dumps(issues))
    f.close()
    logging.info('GIT ISSUES stored in local file')
