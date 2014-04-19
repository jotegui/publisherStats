import json
import urllib2
import logging
from urllib import urlencode
from util import sanity_check, cartodb_query

# Global variables

# API base URLs
gcs_url = 'https://www.googleapis.com/storage/v1beta2'

# Structure of download files
fieldList = ["datasource_and_rights", "type", "modified", "language", "rights", "rightsholder", "accessrights",
             "bibliographiccitation", "references", "institutionid", "collectionid", "datasetid", "institutioncode",
             "collectioncode", "datasetname", "ownerinstitutioncode", "basisofrecord", "informationwithheld",
             "datageneralizations", "dynamicproperties", "occurrenceid", "catalognumber", "occurrenceremarks",
             "recordnumber", "recordedby", "individualid", "individualcount", "sex", "lifestage",
             "reproductivecondition", "behavior", "establishmentmeans", "occurrencestatus", "preparations",
             "disposition", "othercatalognumbers", "previousidentifications", "associatedmedia", "associatedreferences",
             "associatedoccurrences", "associatedsequences", "associatedtaxa", "eventid", "samplingprotocol",
             "samplingeffort", "eventdate", "eventtime", "startdayofyear", "enddayofyear", "year", "month", "day",
             "verbatimeventdate", "habitat", "fieldnumber", "fieldnotes", "eventremarks", "locationid",
             "highergeographyid", "highergeography", "continent", "waterbody", "islandgroup", "island", "country",
             "countrycode", "stateprovince", "county", "municipality", "locality", "verbatimlocality",
             "verbatimelevation", "minimumelevationinmeters", "maximumelevationinmeters", "verbatimdepth",
             "minimumdepthinmeters", "maximumdepthinmeters", "minimumdistanceabovesurfaceinmeters",
             "maximumdistanceabovesurfaceinmeters", "locationaccordingto", "locationremarks", "verbatimcoordinates",
             "verbatimlatitude", "verbatimlongitude", "verbatimcoordinatesystem", "verbatimsrs", "decimallatitude",
             "decimallongitude", "geodeticdatum", "coordinateuncertaintyinmeters", "coordinateprecision",
             "pointradiusspatialfit", "footprintwkt", "footprintsrs", "footprintspatialfit", "georeferencedby",
             "georeferenceddate", "georeferenceprotocol", "georeferencesources", "georeferenceverificationstatus",
             "georeferenceremarks", "geologicalcontextid", "earliesteonorlowesteonothem", "latesteonorhighesteonothem",
             "earliesteraorlowesterathem", "latesteraorhighesterathem", "earliestperiodorlowestsystem",
             "latestperiodorhighestsystem", "earliestepochorlowestseries", "latestepochorhighestseries",
             "earliestageorloweststage", "latestageorhigheststage", "lowestbiostratigraphiczone",
             "highestbiostratigraphiczone", "lithostratigraphicterms", "group", "formation", "member", "bed",
             "identificationid", "identifiedby", "dateidentified", "identificationreferences",
             "identificationverificationstatus", "identificationremarks", "identificationqualifier", "typestatus",
             "taxonid", "scientificnameid", "acceptednameusageid", "parentnameusageid", "originalnameusageid",
             "nameaccordingtoid", "namepublishedinid", "taxonconceptid", "scientificname", "acceptednameusage",
             "parentnameusage", "originalnameusage", "nameaccordingto", "namepublishedin", "namepublishedinyear",
             "higherclassification", "kingdom", "phylum", "class", "order", "family", "genus", "subgenus",
             "specificepithet", "infraspecificepithet", "taxonrank", "verbatimtaxonrank", "scientificnameauthorship",
             "vernacularname", "nomenclaturalcode", "taxonomicstatus", "nomenclaturalstatus", "taxonremarks"]


def get_gcs_object(bucket_name, object_name):
    """Get raw content of object in bucket and parse to record-type object"""

    # Build API url
    url = '/'.join([gcs_url, 'b', bucket_name, 'o', object_name.replace(' ', '%20')])
    url_optim = '?'.join([url, urlencode({'alt': 'media'})])

    # Download object
    raw = urllib2.urlopen(url_optim).read()

    # Prepare storage variables
    d = []
    lines = raw.split("\n")
    pos = 0

    while pos < len(lines):

        splitline = lines[pos].split("\t")

        # Regular line
        if len(splitline) == 160:
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

    query = "select * from query_log where download is not null and download !=''"
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
    b = download.split('/')[2]  # Get Bucket name
    o = download.split('/')[3]  # Get Object name
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


def get_gcs_counts(file_list):
    """Extract institutioncodes and counts for download files in GCS"""
    pubs = {}
    skipped_records = 0

    tot_recs = 0  # Total downloaded records in the whole network

    for f in file_list:
        # Parse name from download field (i.e. remove the gs://vn-downloads part)
        b, o = parse_download_name(f)

        # Download the object or throw a warning and skip
        logging.info('downloading and parsing %s' % o)
        try:
            d = get_gcs_object(b, o)
        except urllib2.HTTPError:
            logging.warning('file {0} not found. Skipping.'.format(o))
            continue

        # Remove headers
        if d[0][0] == fieldList[0]:
            d = d[1:]

        for rec in d:

            tot_recs += 1

            # Option 1 - store by resource directly from the file
            this_ins = rec[fieldList.index('institutioncode')]
            if this_ins == "Royal Ontario Museum: ROM":
                this_ins = "ROM"
            this_col = rec[fieldList.index('datasource_and_rights')].split('=')[1]
            this_url = rec[fieldList.index('datasource_and_rights')]

            # If institutioncode field is empty, take inst and col from resource_staging through url
            if this_ins == '':
                this_url = sanity_check(this_url)
                logging.info("Record without institution code, from {0}".format(this_url))
                this_ins, this_col = get_inst_col(this_url)
                if this_ins is None or this_col is None:
                    skipped_records += 1
                    continue

            # Build internal identifier
            this_pub = '{0}-{1}'.format(this_ins, this_col)

            # Build UUIDs to calculate unique_records
            this_icode = rec[fieldList.index('institutioncode')]
            this_ccode = rec[fieldList.index('collectioncode')]
            this_cnumb = rec[fieldList.index('catalognumber')]
            this_uuid = '{0}/{1}/{2}'.format(this_icode, this_ccode, this_cnumb)

            if this_pub not in pubs:
                # Initialize stats for resource if resource does not exist yet
                pubs[this_pub] = {
                    'url': this_url,  # To extract github org and repo from resource_staging
                    'inst': this_ins,  # Institution code
                    'col': this_col,  # Collection code
                    'download_files': [o],  # Array of individual files, for further calculations
                    'records_downloaded': 1,  # Initial count of records
                    'unique_records': [this_uuid],  # Array of unique records
                    'latlon': {},  # Dictionary of latlon counts. TODO: Update to store country from headers
                    'query': {},  # Dictionary of query terms counts
                    'created': {},  # Dictionary of query dates counts
                    'downloads_in_period': len(file_list),  # Total number of downloads in the given period
                    'this_contrib_count': 1,  # Initial number of retrieved records for this query
                    'this_contrib': []  # Array to store number of records retrieved by each query
                }
            else:
                # If resource exists, add 1 to the record count
                pubs[this_pub]['records_downloaded'] += 1

                # If new download file, append file name and restart this_contrib_count
                if o not in pubs[this_pub]['download_files']:
                    pubs[this_pub]['download_files'].append(o)
                    pubs[this_pub]['this_contrib_count'] = 1
                # If same download file, just add 1 to this_contrib_count
                else:
                    pubs[this_pub]['this_contrib_count'] += 1

                # If UUID not in list of UUIDs, add it
                if this_uuid not in pubs[this_pub]['unique_records']:
                    pubs[this_pub]['unique_records'].append(this_uuid)

        # Once all records from file have been parsed, store this_contrib_count in this_contrib
        for pub in pubs:
            pubs[pub]['this_contrib'].append(pubs[pub]['this_contrib_count'])

    # Once all files have been parsed, store tot_recs
    for pub in pubs:
        pubs[pub]['tot_recs'] = tot_recs

    # Log any skipped record
    if skipped_records > 0:
        logging.warning('{0} skipped records'.format(skipped_records))
    else:
        logging.info('{0} skipped records'.format(skipped_records))
    return pubs


def match_gcs_cdb(pubs, downloads_cdb):
    """Match GCS files with CDB rows"""
    for pub in pubs:
        for dl in downloads_cdb:
            if dl['download'].split("/")[3] in pubs[pub]['download_files']:
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
        idx = pub['download_files'].index(dl['download'].split("/")[3])
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
    query = "select * from query_log"

    query += " where client='portal-prod'"
    query += " and type != 'download' and results_by_resource != '{}' and results_by_resource != ''"

    query = add_time_limit(query=query, today=today, lapse=lapse)  # TODO: uncomment when in prod
    searches = cartodb_query(query)

    pubs = {}

    for search in searches:
        res_count = json.loads(search['results_by_resource'])
        for url in res_count:
            inst, col = get_inst_col(url)
            pub = "{0}-{1}".format(inst, col)
            if pub not in pubs:
                pubs[pub] = {
                    'searches': 1,
                    'records_searched': res_count[url],
                    'list_records_searched': [res_count[url]],
                    'url': url,
                    'inst': inst,
                    'col': col
                }
            else:
                pubs[pub]['searches'] += 1
                pubs[pub]['records_searched'] += res_count[url]
                pubs[pub]['list_records_searched'].append(res_count[url])
            pubs[pub] = get_cdb_stats(search, pubs[pub], from_download=False)

    return pubs


def main(today, lapse='month', testing=False):
    """Extract downloaded files from CartoDB, parse the files in Google Cloud Storage, and build pre-models"""

    # Extract the list of download files for the period
    logging.info('getting data from CartoDB')
    downloads_cdb = get_cdb_downloads(lapse=lapse, today=today)
    file_list = get_file_list(downloads_cdb)

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
