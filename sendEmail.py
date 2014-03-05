import json
import smtplib
import requests
from uploadToGithub import apikey

def getUsers(org):
    key = apikey()
    url = 'https://api.github.com/orgs/{0}/members'.format(org)
    headers = {'User-Agent':'VertNet', 'Authorization': 'token {0}'.format(key)}
    
    r = requests.get(url, headers=headers)
    raw = json.loads(r.content)
    
    users = []
    
    for i in raw:
        users.append(i['login'])
    
    return users

def getEmail(user):
    key = apikey()
    url = 'https://api.github.com/users/{0}'.format(user)
    headers = {'User-Agent':'VertNet', 'Authorization': 'token {0}'.format(key)}
    
    r = requests.get(url, headers=headers)
    raw = json.loads(r.content)
    
    try:
        if type(raw['email']) == type(u''):
            email = raw['email']
        elif type(raw['email']) == type([]) and len(raw['email']) >= 1:
            email = raw['email'][0]
        else:
            email = None
    except:
        email = None
    
    return email

def prepareEmail(toaddr, fromaddr, org, repo, link):
    header = 'To:{0}\nFrom:{1}\nSubject:{2}\n'.format(toaddr, fromaddr, 'Your data usage report is ready!')
    body = """Hello!

Your monthly VertNet data use report is ready! This report has been stored in the GitHub repository of your data resource. Just as a reminder, your github organization is {0} and the repository is {1}. You can see the report, either as a txt or html file, through this link: {2}

This is an automatic message. Therefore, please do not respond to this email. If you have any questions, suggestions or concerns, please send an email to vertnetinfo@vertnet.org <mailto:vertnetinfo@vertnet.org>

Thank you for being part of VertNet!
    
    """.format(org, repo, link)
    
    msg = '{0}\n{1}'.format(header, body)
    
    return msg

def sendEmail(serveraddr, username, password, fromaddr, toaddr, msg):
    
    server = smtplib.SMTP(serveraddr)
    server.starttls()
    server.login(username, password)
    server.sendmail(fromaddr, toaddr, msg)
    server.quit()
    
    return

if __name__ == "__main__":
    
    org = 'mvz-vertnet'
    users = getUsers(org)
    
    for i in users:
        email = getEmail(i)
        print 'User: {0} - Email: {1}'.format(i, email)
    
    toaddr = 'javier.otegui@gmail.com'
    fromaddr = 'mordenvier@gmail.com'
    org = 'pmns-vertnet'
    repo = 'perot-verts'
    link = 'https://github.com/pmns-vertnet/perot-verts/blob/master/reports/PMNS-perot_verts_2014-03-04%2013:06:00.292477.html'
    
    #msg =  prepareEmail(toaddr, fromaddr, org, repo, link)
    
    serveraddr = 'smtp.gmail.com:587'
    username = 'javier.otegui@gmail.com'
    password = open('./email.key', 'r').read().rstrip()
    
    #sendEmail(serveraddr, username, password, fromaddr, toaddr, msg)
