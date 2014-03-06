import os
import json
import jinja2
import urllib2
import logging
from datetime import datetime
import extractStats as es

# Jinja2 is html-oriented, so characters such as < or > appear html-encoded. This function decodes he string when the output is not html, but txt
def unescape(s):
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    s = s.replace("&#34;", "\"")
    # Add more as they appear
    s = s.replace("&amp;", "&")
    return s

def getTimeLapse(lapse = 'month'):
    if lapse == 'full':
        time_lapse = 'since February, 2014'
    else:
        this_year = datetime.now().year
        this_month = datetime.now().month
        if this_month == 1:
            time_lapse = 'for {0}'.format(datetime(this_year-1,12,1).strftime('%B, %Y'))
        else:
            time_lapse = 'for {0}'.format(datetime(this_year,this_month-1,1).strftime('%B, %Y'))
    return time_lapse

# Create the reports
def createReport(pubs, pub, lapse, style = 'txt'):
    
    JINJA_ENVIRONMENT = jinja2.Environment(
        loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
        extensions=['jinja2.ext.autoescape'],
        autoescape=True)
    
    icode = pubs[pub]['inst']
    resname = pubs[pub]['col']
    
    time_lapse = getTimeLapse(lapse)
    
    generated = format(datetime.now(), '%Y/%m/%d')
    
    downloads = len(pubs[pub]['download_files'])
    total_downloads = pubs[pub]['downloads_in_period']
    
    records = pubs[pub]['records_downloaded']
    total_records = pubs[pub]['abs_tot_recs']
    unique_records = len(pubs[pub]['unique_records'])
    
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
    or_countries = countries.keys()
    or_countries.sort()
    q_countries = []
    for i in or_countries:
        q_countries.append([i, countries[i]])
    
    query_dates = {}
    for i in pubs[pub]['created']:
        this_date = i
        this_times = pubs[pub]['created'][i]
        if this_date not in query_dates:
            query_dates[this_date] = this_times
        else:
            query_dates[this_date] += this_times
    or_query_dates = query_dates.keys()
    or_query_dates.sort()
    q_dates = []
    for i in or_query_dates:
        q_dates.append([i,query_dates[i]])
    
    queries = {}
    for i in pubs[pub]['query']:
        this_query = i
        this_times = pubs[pub]['query'][i]
        if this_query not in queries:
            queries[this_query] = this_times
        else:
            queries[this_query] += this_times
    
    template_values = {
                         'icode': icode,
                         'resname': resname,
                         'time_lapse': time_lapse,
                         'generated': generated,
                         'downloads': downloads,
                         'total_downloads': total_downloads,
                         'records': records,
                         'total_records': total_records,
                         'unique_records': unique_records,
                         'len_countries': len(countries),
                         'countries': q_countries,
                         'query_dates': q_dates,
                         'queries': queries
                      }
    
    template = JINJA_ENVIRONMENT.get_template('template.{0}'.format(style))
    report = template.render(template_values)
    
    if style == 'txt':
        report = unescape(report)
    
    return report

def writeReport(report, pub, created_at):
    if not os.path.exists("./reports{0}".format(created_at)):
        os.makedirs("./reports{0}".format(created_at))
    file_name = "./reports{1}/{0}_{1}.txt".format(pub.replace(" ","_"), created_at)
    f = open(file_name, 'w')
    f.write(json.dumps(report))
    f.close()
    
    return

def main(lapse = 'month', testing = False):
    
    pubs = es.main(lapse = lapse, testing = testing)
    
    logging.info('generating reports')
    created_at = format(datetime.now(), '%Y_%m_%d')
    reports = {}
    for pub in pubs:
        reports[pub]={'inst':pubs[pub]['inst'], 'col':pubs[pub]['col'], 'created_at':created_at, 'content_txt':createReport(pubs, pub, lapse, style='txt'), 'content_html':createReport(pubs, pub, lapse, style='html')}
    
    for pub in reports:
        writeReport(reports[pub], pub, created_at)
    
    return reports
