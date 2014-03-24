import json
import urllib2
import logging
from urllib import urlencode
from util import sanityCheck

# Global variables
base_url = 'https://www.googleapis.com/storage/v1beta2'

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

def cartodbQuery(query):
    cartodb_url = 'https://vertnet.cartodb.com/api/v2/sql'
    query_url = '?'.join([cartodb_url, urlencode({'q': query})])
    d = json.loads(urllib2.urlopen(query_url).read())['rows']
    return d

def getObject(bucket_name, object_name):
    """Get raw content of object in bucket and parse to record-type object"""
    url = '/'.join([base_url, 'b', bucket_name, 'o', object_name.replace(' ', '%20')])
    url_optim = '?'.join([url, urlencode({'alt': 'media'})])
    raw = urllib2.urlopen(url_optim).read()
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


def getCDBDownloads(lapse, today):
    """Download the info in the downloads from CDB"""

    query = "select * from query_log where download is not null and download !=''"
    query += " and client='portal-prod'"

    # Default behavior is to extract stats just from the last month
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

    # query_url = '?'.join([cartodb_url, urlencode({'q': query})])

    # d = json.loads(urllib2.urlopen(query_url).read())['rows']

    d = cartodbQuery(query)
    return d


def getFileList(downloads_CDB):
    """Extract list of download file names in GCS"""
    file_list = []
    for d in downloads_CDB:
        file_list.append(d['download'])
    return file_list


def parseDownloadName(download):
    """Parse the download file name"""
    b = download.split('/')[2]
    o = download.split('/')[3]
    return b, o


def getInstColFromURL(url):
    # cartodb_url = "https://vertnet.cartodb.com/api/v2/sql"
    query = "select icode from resource_staging where url={0}".format(url)
    # query_url = '?'.join([cartodb_url, urlencode({'q': query})])
    # query_url = '?q=select%20icode%20from%20resource_staging%20where%20url=%27{0}%27'.format(url)
    d = cartodbQuery(query)
    inst = d[0]['icode']
    col = url.split('?r=')[1]
    return inst, col


def getCountsForPublishers(file_list):
    """Extract institutioncodes and counts for download files in GCS"""
    pubs = {}

    tot_recs = 0  # Total downloaded records in the whole network

    for f in file_list:
        b, o = parseDownloadName(f)
        logging.info('downloading and parsing %s' % o)
        try:
            d = getObject(b, o)
        except:
            logging.warning('file {0} not found. It might be creating at the moment. Skipping.'.format(o))
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

            if this_ins == '':

                # Option 2 - take inst and col from resource_staging through url
                # It takes a lot of time, so leaving it for J.I.C.
                this_url = sanityCheck(this_url)
                logging.info(this_url)
                this_ins, this_col = getInstColFromURL(this_url)
                this_pub = '{0}-{1}'.format(this_ins, this_col)
            else:

                this_pub = '{0}-{1}'.format(this_ins, this_col)

            # Build UUIDs to calculate unique_records
            this_icode = rec[fieldList.index('institutioncode')]
            this_ccode = rec[fieldList.index('collectioncode')]
            this_cnumb = rec[fieldList.index('catalognumber')]
            this_uuid = '{0}/{1}/{2}'.format(this_icode, this_ccode, this_cnumb)

            if this_pub not in pubs:
                # Initialize stats for resource if resource does not exist yet
                pubs[this_pub] = {
                    'url': this_url,
                    'inst': this_ins,
                    'col': this_col,
                    'download_files': [o],  # Array of individual files
                    'records_downloaded': 1,
                    'unique_records': [this_uuid],
                    'latlon': {},
                    'query': {},
                    'created': {},
                    'downloads_in_period': len(file_list),
                    'this_contrib_count': 1,
                    'this_contrib': []
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

    return pubs


def getCDBStatsForPublishers(pubs, downloads_CDB):
    """Match GCS files with CDB rows"""
    for pub in pubs:
        for dl in downloads_CDB:
            if dl['download'].split("/")[3] in pubs[pub]['download_files']:

                latlon = (dl['lat'], dl['lon'])
                created = dl['created_at'].split('T')[0]  # remove the time part
                query = dl['query']
                idx = pubs[pub]['download_files'].index(dl['download'].split("/")[3])

                if latlon not in pubs[pub]['latlon']:
                    pubs[pub]['latlon'][latlon] = 1
                else:
                    pubs[pub]['latlon'][latlon] += 1

                if created not in pubs[pub]['created']:
                    pubs[pub]['created'][created] = 1
                else:
                    pubs[pub]['created'][created] += 1

                if query not in pubs[pub]['query']:
                    pubs[pub]['query'][query] = [1, pubs[pub]['this_contrib'][idx]]
                else:
                    pubs[pub]['query'][query][0] += 1
    return pubs


def main(today, lapse='month', testing = False):
    """Extract downloaded files from CartoDB, parse the files in Google Cloud Storage, and build pre-models"""
    logging.info('getting data from CartoDB')
    downloads_CDB = getCDBDownloads(lapse=lapse, today=today)
    file_list = getFileList(downloads_CDB)

    if testing is True:
        file_list = file_list[:10]

    logging.info('getting data from Google Cloud Storage')
    pubs = getCountsForPublishers(file_list)

    logging.info('generating stats')
    pubs = getCDBStatsForPublishers(pubs, downloads_CDB)

    return pubs
