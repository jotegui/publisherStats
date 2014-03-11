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
        time_lapse = 'ever since February, 2014'
    else:
        this_year = datetime.now().year
        this_month = datetime.now().month
        if this_month == 1:
            time_lapse = '{0}'.format(datetime(this_year-1,12,1).strftime('%B, %Y'))
        else:
            time_lapse = '{0}'.format(datetime(this_year,this_month-1,1).strftime('%B, %Y'))
    return time_lapse

# Build the JSON model
def buildModel(pubs, pub, lapse):
    
    model = {
        "inst": "",
        "col": "",
        "github_org": "",
        "github_repo": "",
        "report_month": "",
        "created_at": "",
        "month": {
            "downloads": 0,
            "downloads_period": 0,
            "records": 0,
            "records_period": 0,
            "records_unique": 0,
            "countries_list": [],
            "countries": [],
            "dates": [],
            "queries": []
        }
    }
    
    inst = pubs[pub]['inst']
    col = pubs[pub]['col']
    model['inst'] = inst
    model['col'] = col
    
    time_lapse = getTimeLapse(lapse)
    model['report_month'] = time_lapse
    
    generated = format(datetime.now(), '%Y/%m/%d')
    model['created_at'] = generated
    
    downloads = len(pubs[pub]['download_files'])
    model['month']['downloads'] = downloads
    total_downloads = pubs[pub]['downloads_in_period']
    model['month']['downloads_period'] = total_downloads
    records = pubs[pub]['records_downloaded']
    model['month']['records'] = records
    total_records = pubs[pub]['tot_recs']
    model['month']['records_period'] = total_records
    unique_records = len(pubs[pub]['unique_records'])
    model['month']['records_unique'] = unique_records
    
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
    #q_countries = []
    for i in or_countries:
        model['month']['countries_list'].append(i)
        model['month']['countries'].append({"country":i, "times":countries[i]})
        #q_countries.append([i, countries[i]])
    
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
    #q_dates = []
    for i in or_query_dates:
        model['month']['dates'].append({"date":i, "times":query_dates[i]})
        #q_dates.append([i,query_dates[i]])
    
    queries = {}
    for i in pubs[pub]['query']:
        this_query = i
        this_values = pubs[pub]['query'][i]
        this_times = this_values[0]
        this_records = this_values[1]
        if this_query not in queries:
            queries[this_query] = [this_times, this_records]
        else:
            queries[this_query][0] += this_times
    for i in queries:
        model['month']['queries'].append({"query":i, "times":queries[i][0], "records":queries[i][1]})
    
    return model

def addYearToModel(model):
    
    path = './reports_2014_01/{0}-{1}.json'.format(model['inst'], model['col'])
    try:
        d = json.loads(open(path, 'r').read().rstrip())
    except:
        return model
    
    if 'year' not in model:
        model['year'] = d['month']
    else:
        for i in d['month']:
            model['year'][i] += d['month'][i]
    
    return model

def addHistoryToModel(model):
    
    path = './reports_2013/{0}-{1}.json'.format(model['inst'], model['col'])
    try:
        d = json.loads(open(path, 'r').read().rstrip())
    except:
        return model
    
    if 'history' not in model:
        model['history'] = d['year']
    else:
        for i in d['year']:
            model['history'][i] += d['year'][i]
    
    return model

# Create the reports
def createReport(model):
    
    JINJA_ENVIRONMENT = jinja2.Environment(
        loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
        extensions=['jinja2.ext.autoescape'],
        autoescape=True)
    
    q_countries = []
    countries = model['month']['countries']
    for i in countries:
        q_countries.append([i['country'], i['times']])
    
    q_dates = []
    dates = model['month']['dates']
    for i in dates:
        q_dates.append([i['date'], i['times']])
    
    q_queries = {}
    queries = model['month']['queries']
    for i in queries:
        if i['query'] not in q_queries:
            q_queries[i['query']] = [i['times'], i['records']]
    
    try:
        m_year_downloads = model['year']['downloads']
        m_year_records = model['year']['records']
    except:
        m_year_downloads = 'No data'
        m_year_records = 'No data'
    try:
        m_hist_downloads = model['history']['downloads']
        m_hist_records = model['history']['records']
    except:
        m_hist_downloads = 'No data'
        m_hist_records = 'No data'
    
    template_values = {
                         'inst': model['inst'],
                         'resname': model['col'],
                         'time_lapse': model['report_month'],
                         'generated': model['created_at'],
                         'downloads': model['month']['downloads'],
                         'total_downloads': model['month']['downloads_period'],
                         'records': model['month']['records'],
                         'total_records': model['month']['records_period'],
                         'unique_records': model['month']['records_unique'],
                         'len_countries': len(model['month']['countries_list']),
                         'countries': q_countries,
                         'query_dates': q_dates,
                         'queries': q_queries,
                         'year_downloads': m_year_downloads,
                         'year_records': m_year_records,
                         'history_downloads': m_hist_downloads,
                         'history_records': m_hist_records
                      }
    
    template_txt = JINJA_ENVIRONMENT.get_template('template.txt')
    report_txt = unescape(template_txt.render(template_values))
    template_html = JINJA_ENVIRONMENT.get_template('template.html')
    report_html = template_html.render(template_values)
    
    return report_txt, report_html

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
    models = {}
    
    for pub in pubs:
        model = buildModel(pubs, pub, lapse)
        model = addYearToModel(model)
        model = addHistoryToModel(model)
        
        report_txt, report_html = createReport(model)
        
        models[pub] = model
        reports[pub]={'inst':pubs[pub]['inst'], 'col':pubs[pub]['col'], 'created_at':created_at, 'content_txt':report_txt, 'content_html':report_html}
    
    #for pub in reports:
    #    writeReport(reports[pub], pub, created_at)
    
    return reports, models
