import json
import urllib2
from urllib import urlencode
from datetime import datetime
from extractStats import get_gcs_counts

base_url = 'https://www.googleapis.com/storage/v1beta2'
downloads_bucket = 'vn-downloads'


# Extract list of files in bucket
def getObjectList(bucket_name):
    url = '/'.join([base_url, 'b', bucket_name, 'o'])
    url = '?'.join([url, urlencode({'fields':'items(name, updated)'})])
    raw = json.loads(urllib2.urlopen(url).read())
    l = []
    for i in raw['items']:
        l.append([i['name'], datetime.strptime(i['updated'].split('T')[0], '%Y-%m-%d')])
    return l


def filterByDate(object_list, year, month = None):
    new_list = []
    for o in object_list:
        if o[1].year != year:
            continue
        elif month is not None and o[1].month != month:
            continue
        else:
            new_list.append("/gs/vn-downloads/{0}".format(o[0]))
    return new_list


def main(year, month = None):
    object_list = getObjectList(downloads_bucket)
    filtered_list = filterByDate(object_list, year, month)
    
    pubs = get_gcs_counts(filtered_list)
    
    if month is None:
        lapse = "year"
    else:
        lapse = "month"
    docs = {}
    for pub in pubs:
        doc = {lapse:{}}
        doc[lapse]['downloads'] = len(pubs[pub]['download_files'])
        doc[lapse]['downloads_period'] = pubs[pub]['downloads_in_period']
        doc[lapse]['records'] = pubs[pub]['records_downloaded']
        doc[lapse]['records_period'] = pubs[pub]['tot_recs']
        docs[pub] = doc
        # json.dump(doc, open('./reports_2013/{0}.json'.format(pub),'w'))
    
    return docs

if __name__ == "__main__":
    
    year = 2013
    month = 12
    doc = main(year, month)
