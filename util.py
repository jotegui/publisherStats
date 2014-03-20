import os
import json

__author__ = 'jotegui'

def apikey(testing):
    """Return credentials file as a JSON object."""
    if testing is False:
        keyname = 'api.key'
    else:
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


def prettyJSON(d):
    print json.dumps(d, sort_keys=True, indent=4, separators=(',', ': '))
    return