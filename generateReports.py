import sys
import urllib2
from urllib import urlencode
import json
from datetime import datetime
import os

# Global variables
base_url = 'https://www.googleapis.com/storage/v1beta2'
data_bucket = 'vn-staging'
downloads_bucket = 'vn-downloads'
fieldList = ["datasource_and_rights", "type", "modified", "language", "rights", "rightsholder", "accessrights", "bibliographiccitation", "references", "institutionid", "collectionid", "datasetid", "institutioncode", "collectioncode", "datasetname", "ownerinstitutioncode", "basisofrecord", "informationwithheld", "datageneralizations", "dynamicproperties", "occurrenceid", "catalognumber", "occurrenceremarks", "recordnumber", "recordedby", "individualid", "individualcount", "sex", "lifestage", "reproductivecondition", "behavior", "establishmentmeans", "occurrencestatus", "preparations", "disposition", "othercatalognumbers", "previousidentifications", "associatedmedia", "associatedreferences", "associatedoccurrences", "associatedsequences", "associatedtaxa", "eventid", "samplingprotocol", "samplingeffort", "eventdate", "eventtime", "startdayofyear", "enddayofyear", "year", "month", "day", "verbatimeventdate", "habitat", "fieldnumber", "fieldnotes", "eventremarks", "locationid", "highergeographyid", "highergeography", "continent", "waterbody", "islandgroup", "island", "country", "countrycode", "stateprovince", "county", "municipality", "locality", "verbatimlocality", "verbatimelevation", "minimumelevationinmeters", "maximumelevationinmeters", "verbatimdepth", "minimumdepthinmeters", "maximumdepthinmeters", "minimumdistanceabovesurfaceinmeters", "maximumdistanceabovesurfaceinmeters", "locationaccordingto", "locationremarks", "verbatimcoordinates", "verbatimlatitude", "verbatimlongitude", "verbatimcoordinatesystem", "verbatimsrs", "decimallatitude", "decimallongitude", "geodeticdatum", "coordinateuncertaintyinmeters", "coordinateprecision", "pointradiusspatialfit", "footprintwkt", "footprintsrs", "footprintspatialfit", "georeferencedby", "georeferenceddate", "georeferenceprotocol", "georeferencesources", "georeferenceverificationstatus", "georeferenceremarks", "geologicalcontextid", "earliesteonorlowesteonothem", "latesteonorhighesteonothem", "earliesteraorlowesterathem", "latesteraorhighesterathem", "earliestperiodorlowestsystem", "latestperiodorhighestsystem", "earliestepochorlowestseries", "latestepochorhighestseries", "earliestageorloweststage", "latestageorhigheststage", "lowestbiostratigraphiczone", "highestbiostratigraphiczone", "lithostratigraphicterms", "group", "formation", "member", "bed", "identificationid", "identifiedby", "dateidentified", "identificationreferences", "identificationverificationstatus", "identificationremarks", "identificationqualifier", "typestatus", "taxonid", "scientificnameid", "acceptednameusageid", "parentnameusageid", "originalnameusageid", "nameaccordingtoid", "namepublishedinid", "taxonconceptid", "scientificname", "acceptednameusage", "parentnameusage", "originalnameusage", "nameaccordingto", "namepublishedin", "namepublishedinyear", "higherclassification", "kingdom", "phylum", "class", "order", "family", "genus", "subgenus", "specificepithet", "infraspecificepithet", "taxonrank", "verbatimtaxonrank", "scientificnameauthorship", "vernacularname", "nomenclaturalcode", "taxonomicstatus", "nomenclaturalstatus", "taxonremarks"]

# Extract list of files in bucket
def getObjectList(bucket_name):
    url = '/'.join([base_url, 'b', bucket_name, 'o'])
    url_optim = '?'.join([url, urlencode({'fields':'items(name)'})])
    raw = json.loads(urllib2.urlopen(url_optim).read())
    l = []
    for i in raw['items']:
        l.append(i['name'])
    return l

# Get raw content of object in bucket and parse to record-type object
def getObject(bucket_name, object_name):
    url = '/'.join([base_url, 'b', bucket_name, 'o', object_name.replace(' ','%20')])
    url_optim = '?'.join([url, urlencode({'alt':'media'})])
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
        elif len(splitline) < 160 and len(splitline) + len(lines[pos+1].split("\t")) == 161:
            d.append(lines[pos].split("\t")[:-1] + lines[pos+1].split("\t"))
            pos += 1

        # Two records in three lines
        elif len(splitline) < 160 and len(splitline) + len(lines[pos+1].split("\t")) > 161:
            line1 = splitline[:-1]+lines[pos+1].split("\t")[:(160-len(splitline))]
            line1.append("")
            d.append(line1)
            line2 = lines[pos+1].split("\t")[(160-len(splitline)):-1]+lines[pos+2].split("\t")
            pos += 2

        pos += 1
    return d

# Download the info in the downloads from CDB
def getCDBDownloads(lapse):
    query_url = 'https://vertnet.cartodb.com/api/v2/sql?q=select%20*%20from%20query_log%20where%20download%20is%20not%20null%20and%20download%20!=%27%27'

    # Default behavior is to extract stats just from the last month
    if lapse == 'month':
        this_year = datetime.now().year
        this_month = datetime.now().month
        if this_month == 1:
            limit_year = this_year - 1
            limit_month = 12
        else:
            limit_year = this_year
            limit_month = this_month - 1
        limit_string = '%20and%20extract%28year%20from%20created_at%29%20=%20{0}%20and%20extract%28month%20from%20created_at%29%20=%20{1}'.format(limit_year, limit_month)
        query_url += limit_string
    
    d = json.loads(urllib2.urlopen(query_url).read())['rows']
    return d

# Extract list of download file names in GCS
def getFileList(downloads_CDB):
    file_list = []
    for d in downloads_CDB:
        file_list.append(d['download'])
    return file_list

# Parse the download file name
def parseDownloadName(download):
    b = download.split('/')[2]
    o = download.split('/')[3]
    return b, o

# Extract institutioncodes and counts for download files in GCS
def getCountsForPublishers(file_list):
    pubs = {}
    abs_tot_recs = 0
    
    for f in file_list:
        b, o = parseDownloadName(f)
        print 'downloading and parsing %s' % o
        try:
            d = getObject(b, o)
        except:
            print 'file not found. It might be creating at the moment. Skipping.'
            continue
    
        # Remove headers
        if d[0][0] == fieldList[0]:
            d = d[1:]
        
        tot_recs = 0
        
        for rec in d:
            
            tot_recs += 1
            abs_tot_recs += 1
            
            # Option 1 - store by resource
            this_ins = rec[fieldList.index('institutioncode')]
            if this_ins == "Royal Ontario Museum: ROM":
                this_ins = "ROM"
            this_col = rec[fieldList.index('datasource_and_rights')].split('=')[1]
            this_pub = '{0}-{1}'.format(this_ins, this_col)
            
            # Option 2 - store by institution
            #this_pub = rec[fieldList.index('institutioncode')]
            #if this_pub == "Royal Ontario Museum: ROM":
            #    this_pub = "ROM"
            
            this_icode = rec[fieldList.index('institutioncode')]
            this_ccode = rec[fieldList.index('collectioncode')]
            this_cnumb = rec[fieldList.index('catalognumber')]
            this_uuid = '{0}/{1}/{2}'.format(this_icode, this_ccode, this_cnumb)
            
            if this_pub not in pubs:
                pubs[this_pub] = {
                                    'inst':this_ins,
                                    'col':this_col,
                                    'download_files':[o],
                                    'records_downloaded':1,
                                    'unique_records':[this_uuid],
                                    'latlon':{},
                                    'query':{},
                                    'created':{},
                                    'downloads_in_period':len(file_list),
                                    'this_contrib': 1,
                                    'avg_contrib': []
                                  }
            else:
                pubs[this_pub]['records_downloaded'] += 1
                
                if o not in pubs[this_pub]['download_files']:
                    pubs[this_pub]['download_files'].append(o)
                    pubs[this_pub]['this_contrib'] = 1
                else:
                    pubs[this_pub]['this_contrib'] += 1
                
                if this_uuid not in pubs[this_pub]['unique_records']:
                    pubs[this_pub]['unique_records'].append(this_uuid)
        
        for pub in pubs:
            pubs[pub]['avg_contrib'].append(pubs[pub]['this_contrib']*100.0/tot_recs)
    for pub in pubs:
        pubs[pub]['abs_tot_recs'] = abs_tot_recs
    return pubs

# Match GCS files with CDB rows
def getCDBStatsForPublishers(pubs, downloads_CDB):
    for pub in pubs:
        for dl in downloads_CDB:
            if dl['download'].split("/")[3] in pubs[pub]['download_files']:
                
                latlon = (dl['lat'],dl['lon'])
                created = dl['created_at']
                query = dl['query']
                
                if latlon not in pubs[pub]['latlon']:
                    pubs[pub]['latlon'][latlon] = 1
                else:
                    pubs[pub]['latlon'][latlon] += 1
                
                if created not in pubs[pub]['created']:
                    pubs[pub]['created'][created] = 1
                else:
                    pubs[pub]['created'][created] += 1
                
                if query not in pubs[pub]['query']:
                    pubs[pub]['query'][query] = 1
                else:
                    pubs[pub]['query'][query] += 1
    return pubs

# Create the reports
def createReport(pubs, pub, lapse):
    
    # Header
    if lapse == 'full':
        timelapse = 'since February, 2014'
    else:
        this_year = datetime.now().year
        this_month = datetime.now().month
        if this_month == 1:
            timelapse = 'for {0}'.format(datetime(this_year-1,12,1).strftime('%B, %Y'))
        else:
            timelapse = 'for {0}'.format(datetime(this_year,this_month-1,1).strftime('%B, %Y'))
    report = "Report for Institution Code {0}, Resource {1}\nUsage stats {2}, generated on {3}\n\n".format(pubs[pub]['inst'], pubs[pub]['col'], timelapse, format(datetime.now(), '%Y/%m/%d'))
    
    # Downloads and records
    downloads = len(pubs[pub]['download_files'])
    unique_records = len(pubs[pub]['unique_records'])
    avg_contrib = round(sum(pubs[pub]['avg_contrib'])*1.0/len(pubs[pub]['avg_contrib']), 2)
    
    report += "Number of download events that retrieved data from the resource: {0} (out of {1} download event in this period)\n".format(downloads, pubs[pub]['downloads_in_period'])
    records = pubs[pub]['records_downloaded']
    abs_tot_recs = pubs[pub]['abs_tot_recs']
    report += "Total number of records downloaded: {0} (out of {1} records downloaded for all resources in this period)\n".format(records, abs_tot_recs)
    report += "Total number of unique records downloaded: {0}\n".format(unique_records)
    #report += "Average contribution to a download event: {0}%\n".format(avg_contrib)
    
    # Geography of the queries
    report += "\nOrigin of the queries that retrieved data from the resource:\n"
    countries = {}
    for i in pubs[pub]['latlon']:
        lat = i[0]
        lon = i[1]
        geonames_url = 'http://api.geonames.org/countryCodeJSON?formatted=true&lat={0}&lng={1}&username=jotegui&style=full'.format(lat, lon)
        country = json.loads(urllib2.urlopen(geonames_url).read())['countryName']
        if country not in countries:
            countries[country] = pubs[pub]['latlon'][i]
        else:
            countries[country] += pubs[pub]['latlon'][i]
    for country in countries:
        report += "\tCountry: {0} ; Number of times: {1}\n".format(country, countries[country])
    
    # Time of the queries
    report += "\nDates of the queries that retrieved data from the resource:\n"
    for i in pubs[pub]['created']:
        report += "\tDate: {0} ; Number of times: {1}\n".format(format(datetime.strptime(i, '%Y-%m-%dT%H:%M:%SZ'), '%Y/%m/%d - %H:%M:%S'), pubs[pub]['created'][i])
        
    # List of queries
    report += "\nList of queries that retrieved data from the resource:\n"
    for i in pubs[pub]['query']:
        report += "\tQuery: \"{0}\" ; Number of times: {1}\n".format(i, pubs[pub]['query'][i])
    
    # Store report in file
    report += "\nEnd of report."
    
    # Return report string
    print 'finished report for {0}'.format(pub)
    return report

def writeReport(report, pub, created_at):
    if not os.path.exists("./reports"):
        os.makedirs("./reports")
    file_name = "./reports/{0}_{1}.txt".format(pub.replace(" ","_"), created_at)
    f = open(file_name, 'w')
    f.write(report)
    f.close()
    
    return

# Main function
def main(created_at = format(datetime.now(), '%Y_%m_%d'), lapse = 'month', testing = False):
        
    print 'getting data from CartoDB'
    downloads_CDB = getCDBDownloads(lapse)
    file_list = getFileList(downloads_CDB)
    
    if testing is True:
        file_list = file_list[:10]
    
    print 'getting data from Google Cloud Storage'
    pubs = getCountsForPublishers(file_list)
    
    print 'generating stats'
    pubs = getCDBStatsForPublishers(pubs, downloads_CDB)
    
    print 'generating reports'
    reports = {}
    for pub in pubs:
        reports[pub]={'inst':pubs[pub]['inst'], 'col':pubs[pub]['col'], 'created_at':created_at, 'content':createReport(pubs, pub, lapse)}
    
    return reports
    
#if __name__ == "__main__":
#    
#    ini = datetime.now()
#    
#    try:
#        lapse = sys.argv[1]
#        if lapse != 'full':
#            lapse = 'month'
#    except IndexError:
#        lapse = 'month'
#    
#    created_at = format(datetime.now(), '%Y_%m_%d')
#    
#    reports = main(created_at=created_at, lapse=lapse, testing=False)
#    
#    print 'storing reports'
#    for pub in reports:
#        writeReport(reports[pub]['content'], pub, reports[pub]['created_at'])

#    
#    end = datetime.now()
#    dif = end - ini
#    
#    print "elapsed: {0}".format(dif)
#    print 'done'
