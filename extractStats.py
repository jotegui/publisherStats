import json
import urllib2
import logging
from urllib import urlencode
from util import sanity_check, cartodb_query
from fieldLists import fieldList_160, fieldList_176

__author__ = '@jotegui'


# Global variables

# API base URLs
gcs_url = 'https://www.googleapis.com/download/storage/v1'



def get_gcs_object(b, o):
    """Get raw content of object in bucket and parse to record-type object"""

    # Build API url
    url = '/'.join([gcs_url, 'b', b, 'o', o.replace(' ', '%20')])
    url_optim = '?'.join([url, urlencode({'alt': 'media'})])

    # Download object
    raw = urllib2.urlopen(url_optim).read()

    # Prepare storage variables
    d = []
    lines = raw.split("\n")
    if len(lines[-1]) <= 1:
        lines = lines[:-1]
    pos = 0

    while pos < len(lines):
        splitline = lines[pos].split("\t")

        # Ignore empty lines
        if len(splitline) == 1 and splitline[0] == "":
            pass

        # Regular line
        elif len(splitline) == 160:
            d.append(splitline)
        
        # Regular, new-schema-like line
        elif len(splitline) == 176:
            d.append(splitline)

        # Two records in one line
        elif len(splitline) == 319:
            line1 = splitline[:159]
            line1.append("")
            d.append(line1)
            line2 = splitline[159:]
            d.append(line2)

        # One record in two lines
        elif len(splitline) < 160 and len(splitline) + len(lines[pos + 1].split("\t")) == 161:
            d.append(lines[pos].split("\t")[:-1] + lines[pos + 1].split("\t"))
            pos += 1

        # Two records in three lines
        elif len(splitline) < 160 and len(splitline) + len(lines[pos + 1].split("\t")) > 161:
            line1 = splitline[:-1] + lines[pos + 1].split("\t")[:(160 - len(splitline))]
            line1.append("")
            d.append(line1)
            line2 = lines[pos + 1].split("\t")[(160 - len(splitline)):-1] + lines[pos + 2].split("\t")
            d.append(line2)
            pos += 2

        # Ignore the rest!

        pos += 1
    return d


def add_time_limit(query, today, lapse='month'):
    """Add time limit to CartoDB query. Default behavior is to extract stats from just the last month"""

    if lapse == 'month':
        this_year = today.year
        this_month = today.month
        if this_month == 1:
            limit_year = this_year - 1
            limit_month = 12
        else:
            limit_year = this_year
            limit_month = this_month - 1
        limit_string = " and extract(year from created_at)={0}".format(limit_year)
        limit_string += " and extract(month from created_at)={0}".format(limit_month)
        query += limit_string

    return query


def get_cdb_downloads(lapse, today):
    """Download the info in the downloads from CDB"""

    query = "select * from query_log_master where type='download' and download is not null and download !=''"
    query += " and client='portal-prod'"  # Just production portal downloads

    query = add_time_limit(query=query, today=today, lapse=lapse)  # Just from the specific month
    d = cartodb_query(query)
    return d


def get_file_list(downloads_cdb):
    """Extract list of download file names in GCS"""
    file_list = []
    for d in downloads_cdb:
        file_list.append(d['download'])
    return file_list


def parse_download_name(download):
    """Parse the download file name"""
    elements = download.split('/')
    try:
        if elements[1] == u'gs':
            bucket_idx = 2
            object_idx = 3
        elif elements[1].startswith("vn-"):
            bucket_idx = 1
            object_idx = 2
    except IndexError:
        return None, None
    b = download.split('/')[bucket_idx]  # Get Bucket name
    o = download.split('/')[object_idx]  # Get Object name
    return b, o


def get_inst_col(url):
    query = "select icode from resource_staging where url='{0}'".format(url)
    max_retries = 3
    retry = 0
    while retry < max_retries:
        d = cartodb_query(query)
        if len(d) > 0:
            inst = d[0]['icode']
            col = url.split('?r=')[1]
            return inst, col
        else:
            retry += 1
    return None, None


def extract_file_content(f):
    # Parse name from download field
    b, o = parse_download_name(f)
    if b is None or o is None:
        logging.warning('bucket and/or object name missing in record. Skipping')
        return None, None
    elif b == 'vn-dltest':
        logging.info('file {0} was for testing purposes. Not existing anymore. Skipping'.format(f))
        return None, None

    # Download the object or throw a warning and skip
    logging.info('downloading and parsing %s' % o)
    try:
        d = get_gcs_object(b, o)
    except urllib2.HTTPError:
        logging.warning('file {0} not found. Skipping.'.format(f))
        return None, None
    except MemoryError:
        logging.warning('file {0} too large to download. Skipping'.format(f))
        return None, None

    # Ignore empty files (failed tests)
    if len(d) == 0:
        logging.info('file {0} does not correspond to any valid schema. Ignoring'.format(f))
        return None, None

    # Remove headers
    if len(d[0]) == 160:
        fieldList = fieldList_160
    elif len(d[0]) == 176:
        fieldList = fieldList_176

    if d[0][0] == fieldList[0]:
        d = d[1:]

    return fieldList, d

def process_record(rec, headers):
    res = {}

    if len(headers) == 160:
        url_field = 'datasource_and_rights'
    elif len(headers) == 176 :
        url_field = 'dataset_url'

    # Extract and sanitize URL
    url = rec[headers.index(url_field)]
    if url == "" and len(headers) == 176:
        q = "select url from resource_staging where gbifdatasetid='{0}'".format(rec[headers.index('gbifdatasetid')])
        url = cartodb_query(q)[0]['url']
    url = sanity_check(url)

    # Store by resource directly from the file
    this_ins = rec[headers.index('institutioncode')]
    if this_ins.startswith("Royal Ontario Museum"):
        this_ins = "ROM"
    elif this_ins.startswith('Borror Laboratory of Bioacoustics'):
        this_ins = 'BLB'
    elif this_ins.startswith('Ohio State University'):
        this_ins = 'OSUM'
    this_col = url.split('=')[1]
    
    # If institutioncode field is empty, take inst and col from resource_staging through url
    if this_ins == '':
        logging.info("record without institution code, from {0}".format(url))
        this_ins, this_col = get_inst_col(url)
        if this_ins is None or this_col is None:
            logging.warning("could not identify resource. Skipping record")
            return None

    # Build internal identifier
    pub = '{0}-{1}'.format(this_ins, this_col)

    # Build UUIDs to calculate unique_records
    icode = rec[headers.index('institutioncode')]
    ccode = rec[headers.index('collectioncode')]
    cnumb = rec[headers.index('catalognumber')]
    uuid = '{0}/{1}/{2}'.format(icode, ccode, cnumb)

    if 'gbifdatasetid' in headers:
        gbifdatasetid = rec[headers.index('gbifdatasetid')]
    else:
        gbifdatasetid = None

    res['id'] = pub
    res['icode'] = icode
    res['ccode'] = ccode
    res['cnumb'] = cnumb
    res['uuid'] = uuid
    res['url'] = url
    res['gbifdatasetid'] = gbifdatasetid

    return res


def process_file(f):
    
    pubs = {}
    skipped_records = 0
    file_records = 0

    # Extract the content of the file or return None
    h, d = extract_file_content(f)
    if d is None:
        return None, None, None

    # Process each record
    for rec in d:
        res = process_record(rec, h)
        if res is None:
            skipped_records += 1
            continue

        if res['id'] not in pubs:
            # Initialize stats for resource if resource does not exist yet
            pubs[res['id']] = {
                'gbifdatasetid': res['gbifdatasetid'],
                'url': res['url'],  # To extract github org and repo from resource_staging
                'inst': res['icode'],  # Institution code
                'col': res['ccode'],  # Collection code
                'download_files': [f],  # Array of individual files, for further calculations
                'records_downloaded': 1,  # Initial count of records
                'unique_records': set([res['uuid']]),  # Array of unique records
                'latlon': {},  # Dictionary of latlon counts. TODO: Update to store country from headers
                'query': {},  # Dictionary of query terms counts
                'created': {},  # Dictionary of query dates counts
                # 'this_contrib_count': 1,  # Initial number of retrieved records for this query
                'this_contrib': []  # Array to store number of records retrieved by each query
            }
        else:
            # If resource exists, add 1 to the record count
            pubs[res['id']]['records_downloaded'] += 1

            # # If new download file, append file name and restart this_contrib_count
            # if f not in pubs[res['id']]['download_files']:
            #     pubs[res['id']]['download_files'].append(f)
            #     pubs[res['id']]['this_contrib_count'] = 1
            # # If same download file, just add 1 to this_contrib_count
            # else:
            #     pubs[res['id']]['this_contrib_count'] += 1

            # If UUID not in list of UUIDs, add it
            # if res['uuid'] not in pubs[res['id']]['unique_records']:
            pubs[res['id']]['unique_records'] = pubs[res['id']]['unique_records'].union([res['uuid']])

        file_records += 1

        
    # Once all records from file have been parsed, store records_downloaded in this_contrib
    for pubid in pubs:
        pubs[pubid]['this_contrib'].append(pubs[pubid]['records_downloaded'])

    return pubs, file_records, skipped_records


def get_gcs_counts(file_list):
    """Extract institutioncodes and counts for download files in GCS"""
    
    pubs = {}
    total_skipped_records = 0
    total_records = 0  # Total downloaded records in the whole network

    for f in file_list:
        # Extract data from file
        p, file_records, skipped_records = process_file(f)
        if p is None:
            continue

        # Merge with already parsed files
        for pubid in p:
            # If first time of the resource
            if pubid not in pubs:
                pubs[pubid] = p[pubid]
            # Otherwise
            else:
                # Append download file to download_files
                pubs[pubid]['download_files'].append(f)
                # Append record count to this_contrib
                pubs[pubid]['this_contrib'].append(p[pubid]['records_downloaded'])
                # Add unique records to set
                pubs[pubid]['unique_records'] = pubs[pubid]['unique_records'].union(p[pubid]['unique_records'])
                # Try to add gbifdatasetid
                if pubs[pubid]['gbifdatasetid'] is None and p[pubid]['gbifdatasetid'] is not None:
                    pubs[pubid]['gbifdatasetid'] = p[pubid]['gbifdatasetid']


        total_skipped_records += skipped_records
        total_records += file_records

    # Once all files have been parsed, store total_records and downloads_in_period and calculate records_downloaded
    for pub in pubs:
        pubs[pub]['tot_recs'] = total_records
        pubs[pub]['downloads_in_period'] = len(file_list)
        pubs[pub]['records_downloaded'] = sum(pubs[pub]['this_contrib'])

    # Log any skipped record
    if total_skipped_records > 0:
        logging.warning('{0} skipped records'.format(total_skipped_records))
    else:
        logging.info('{0} skipped records'.format(total_skipped_records))
    return pubs


def match_gcs_cdb(pubs, downloads_cdb):
    """Match GCS files with CDB rows"""
    for pub in pubs:
        for dl in downloads_cdb:
            if dl['download'] in pubs[pub]['download_files']:
                pubs[pub] = get_cdb_stats(dl=dl, pub=pubs[pub], from_download=True)
    return pubs


def get_cdb_stats(dl, pub, from_download=False):
    """Apply values from CartoDB record to resource stats"""

    latlon = (dl['lat'], dl['lon'])
    created = dl['created_at'].split('T')[0]  # Remove the time part, keep just date
    query = dl['query']

    # Store latlon counts
    if 'latlon' not in pub:
        pub['latlon'] = {latlon: 1}
    elif latlon not in pub['latlon']:
        pub['latlon'][latlon] = 1
    else:
        pub['latlon'][latlon] += 1

    # Store query date counts
    if 'created' not in pub:
        pub['created'] = {created: 1}
    elif created not in pub['created']:
        pub['created'][created] = 1
    else:
        pub['created'][created] += 1

    # Store query terms and records retrieved for this particular query
    if from_download is True:
        idx = pub['download_files'].index(dl['download'])
        val = pub['this_contrib'][idx]
    else:
        val = pub['list_records_searched'][-1]

    if 'query' not in pub:
        pub['query'] = {query: [1, val]}
    elif query not in pub['query']:
        pub['query'][query] = [1, val]
    else:
        pub['query'][query][0] += 1

    return pub


def get_cdb_searches(today, lapse='month'):
    query = "select * from query_log_master"

    query += " where client='portal-prod'"
    query += " and type != 'download'"
    query += " and results_by_resource != '{}' and results_by_resource != ''"

    query = add_time_limit(query=query, today=today, lapse=lapse)

    searches = cartodb_query(query)

    pubs = {}

    for search in searches:
        res_count = json.loads(search['results_by_resource'])
        
        for url in res_count:
            if not url.startswith('http'):
                gbifdatasetid = url
                q = "select url from resource_staging where gbifdatasetid='{0}'".format(gbifdatasetid)
                ident = (gbifdatasetid, cartodb_query(q)[0]['url'])
            else:
                ident = (url, url)

            inst, col = get_inst_col(ident[1])
            pub = "{0}-{1}".format(inst, col)
            if pub not in pubs:
                pubs[pub] = {
                    'searches': 1,
                    'records_searched': res_count[ident[0]],
                    'list_records_searched': [res_count[ident[0]]],
                    'url': ident[1],
                    'gbifdatasetid': ident[0] if ident[0]!=ident[1] else None,
                    'inst': inst,
                    'col': col
                }
            else:
                pubs[pub]['searches'] += 1
                pubs[pub]['records_searched'] += res_count[ident[0]]
                pubs[pub]['list_records_searched'].append(res_count[ident[0]])
            pubs[pub] = get_cdb_stats(search, pubs[pub], from_download=False)

    return pubs


def main(today, lapse='month', testing=False):
    """Extract downloaded files from CartoDB, parse the files in Google Cloud Storage, and build pre-models"""

    # Extract the list of download files for the period
    logging.info('getting data from CartoDB')
    downloads_cdb = get_cdb_downloads(lapse=lapse, today=today)
    file_list = get_file_list(downloads_cdb)
    
    # Limit to the first ten downloads if on testing mode
    if testing is True:
        file_list = file_list[:10]

    # Extract the GCS stats for each download file in file_list
    logging.info('getting data from Google Cloud Storage')
    pubs = get_gcs_counts(file_list)

    # Extract the CDB stats for each resource in pubs
    logging.info('generating download stats')
    pubs = match_gcs_cdb(pubs, downloads_cdb)

    # Extract CDB stats for searches
    logging.info('getting counts for searches')
    searches = get_cdb_searches(today=today, lapse=lapse)

    # Integrate searches and downloads
    logging.info('integrating searches stats')
    for pub in searches:
        if pub not in pubs:
            pubs[pub] = {'searches': searches[pub]}
            pubs[pub]['url'] = searches[pub]['url']
            pubs[pub]['inst'] = searches[pub]['inst']
            pubs[pub]['col'] = searches[pub]['col']
        else:
            pubs[pub]['searches'] = searches[pub]

    return pubs
