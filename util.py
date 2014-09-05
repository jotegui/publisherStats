import os
import json
import urllib2
import logging
from urllib import urlencode

__author__ = '@jotegui'


def apikey(testing):
    """Return credentials file as a JSON object."""
    if testing is False:
        keyname = 'api.key'  # If not in testing mode, get VertNet repo API key
    else:
        keyname = 'JOT.key'  # If in testing mode, get jotegui repo API key
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), keyname)
    key = open(path, "r").read().rstrip()
    return key


def sanity_check(url):
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
    elif url == 'http://ipt.vertnet.org:8080/ipt/resource.do?r=ncsmvertpaleo':
        new_url = 'http://ipt.vertnet.org:8080/ipt/resource.do?r=ncsm_vertpaleo'
    elif url == 'http://ipt.vertnet.org:8080/ipt/resource.do?r=ncsm-mammals':
        new_url = 'http://ipt.vertnet.org:8080/ipt/resource.do?r=ncsm_mammals'
    # More to be added as needed
    else:
        new_url = url

    return new_url


def pretty_json(d):
    """Print a JSON string in pretty format."""
    print json.dumps(d, sort_keys=True, indent=4, separators=(',', ': '))
    return


def api_query(api_url, params, res_field):
    """Launch query to an API with the specified query and retrieve the specified field."""
    query_url = '?'.join([api_url, urlencode(params)])
    max_retries = 5
    retry = 0
    while retry < max_retries:
        try:
            d = json.loads(urllib2.urlopen(query_url).read())[res_field]
            return d
        except urllib2.HTTPError:
            retry += 1
        except ValueError:
            retry += 1
    return []


def cartodb_query(query):
    """Build parameters for launching a query to the CartoDB API."""
    api_url = 'https://vertnet.cartodb.com/api/v2/sql'
    params = {'q': query}
    res_field = 'rows'
    d = api_query(api_url=api_url, params=params, res_field=res_field)
    return d


def geonames_query(lat, lon):
    """Build parameters for launching a query to the GeoNames API."""
    api_url = 'http://api.geonames.org/countryCodeJSON'
    params = {
        'formatted': 'true',
        'lat': lat,
        'lng': lon,
        'username': 'jotegui',
        'style': 'full'
    }
    res_field = 'countryName'
    d = api_query(api_url=api_url, params=params, res_field=res_field)
    return d


def get_org_repo(url):
    """Extract github organization and repository by datasource url from CartoDB table"""
    url = sanity_check(url)
    query = "select github_orgname, github_reponame from resource_staging where url='{0}'".format(url)

    try:
        d = cartodb_query(query)[0]
        org = d['github_orgname']
        repo = d['github_reponame']
    except IndexError:
        logging.error('Getting Org and Repo by URL failed with url {0}'.format(url))
        org = None
        repo = None
    return org, repo


def unescape(s):
    """Replace encoded characters"""
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    s = s.replace("&#34;", "\"")
    # Add more as they appear
    s = s.replace("&amp;", "&")
    return s
