import os
import json
import base64
import jinja2
import urllib2
import logging
import requests
from datetime import datetime


def unescape(s):
    """Jinja2 is html-oriented, so characters such as < or > appear html-encoded.
This function decodes he string when the output is not html, but txt."""
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    s = s.replace("&#34;", "\"")
    # Add more as they appear
    s = s.replace("&amp;", "&")
    return s


def getTimeLapse(lapse = 'month'):
    if lapse == 'full':
        report_month_string = 'ever since February, 2014'
        report_month = '2014/02'
    else:
        this_year = datetime.now().year
        this_month = datetime.now().month
        if this_month == 1:
            report_month_string = '{0}'.format(datetime(this_year - 1, 12, 1).strftime('%B, %Y'))
            report_month = '{0}'.format(datetime(this_year - 1, 12, 1).strftime('%Y/%m'))
        else:
            report_month_string = '{0}'.format(datetime(this_year, this_month - 1, 1).strftime('%B, %Y'))
            report_month = '{0}'.format(datetime(this_year, this_month - 1, 1).strftime('%Y/%m'))
    return report_month_string, report_month


def findLastReport(inst, col):
    pub = '-'.join([inst, col])
    try:
        models = json.loads(open('./modelURLs.json','r').read().rstrip())[pub]
        last_url = models[-1]
    except:
        last_url = ''
    return last_url

def buildModel(pubs, pub, lapse):
    """Build the JSON model with data about the month for the resource"""

    model = {
        "url": "",  # IPT resource URL, to link with CartoDB resource_staging table
        "inst": "",  # Institution Code
        "col": "",  # Collection code
        "github_org": "",  # GitHub Organization
        "github_repo": "",  # GitHub Repository
        "report_month_string": "",  # String to add to the reports, something like "February, 2014"
        "report_month": "",  # Compact mode of report_month, something like "2014/02"
        "last_report_url": "",  # link to last existing report in GitHub, or empty if first time
        "created_at": "",  # Full date of creation, like "2014/03/17"
        "month": {  # Monthly values
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

    url = pubs[pub]['url']
    inst = pubs[pub]['inst']
    col = pubs[pub]['col']
    model['url'] = url
    model['inst'] = inst
    model['col'] = col

    report_month_string, report_month = getTimeLapse(lapse)
    model['report_month_string'] = report_month_string
    model['report_month'] = report_month

    model['last_report_url'] = findLastReport(inst, col)

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
        geonames_url = 'http://api.geonames.org/countryCodeJSON?formatted=true&lat={0}&lng={1}&username=jotegui&style=full'.format(
            lat, lon)
        country = json.loads(urllib2.urlopen(geonames_url).read())['countryName']
        if country not in countries:
            countries[country] = pubs[pub]['latlon'][i]
        else:
            countries[country] += pubs[pub]['latlon'][i]
    or_countries = countries.keys()
    or_countries.sort()
    for i in or_countries:
        model['month']['countries_list'].append(i)
        model['month']['countries'].append({"country": i, "times": countries[i]})

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
    for i in or_query_dates:
        model['month']['dates'].append({"date": i, "times": query_dates[i]})

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
        model['month']['queries'].append({"query": i, "times": queries[i][0], "records": queries[i][1]})

    return model


def addPastDataToModel(model):
    """Add year and history cummulative values"""

    # First, put the previous month's year and history objects in the month model

    # If it's the first time, take 2013 and 2014/01 values from files
    if model['last_report_url'] == "":
        model = addInitialYearToModel(model)
        model = addInitialHistoryToModel(model)

    # Else, take values from last month's json
    else:
        # org = 'jotegui'  # Comment if JSON files are stored in the resource's repo
        # repo = 'statReports'  # Comment if JSON files are stored in the resource's repo
        # org = model['github_org']  # Uncomment if JSON files are stored in the resource's repo
        # repo = model['github_repo']  # Uncomment if JSON files are stored in the resource's repo
        #
        # path = "{0}-{1}_{2}".format(model['inst'], model['col'], model['last_report'].replace('/','_'))
        #
        # if org == 'jotegui':
        #     path = 'data/{0}'.format(path)
        # else:
        #     path = 'data/{0}'.format(path)

        url = model['last_report_url']
        # print url

        r = requests.get(url)

        if r.status_code == 200:

            prev_model = json.loads(base64.b64decode(json.loads(r.content)['content']))
            model['year'] = prev_model['year']
            model['history'] = prev_model['history']

    # Now, add monthly values to history and to year if still in same year

    for t in ['history', 'year']:

        # If report for first month of year, reset counts to monthly values
        if t == 'year' and model['report_month'][-2:] == '01':
            for i in model['month']:
                model[t][i] = model['month'][i]
        else:
            # Add basic counts
            model[t]['downloads'] += model['month']['downloads']
            model[t]['downloads_period'] += model['month']['downloads_period']
            model[t]['records'] += model['month']['records']
            model[t]['records_period'] += model['month']['records_period']

            # Append any non-existing country to list
            if 'countries_list' in model[t]:
                for c in model['month']['countries_list']:
                    if c not in model[t]['countries_list']:
                        model[t]['countries_list'].append(c)
            else:
                model[t]['countries_list'] = model['month']['countries_list']

            # Add Countries and Dates counts. Same for Queries, but if record count is modified, update it
            for d in ['countries', 'dates', 'queries']:
                if d not in model[t]:
                    model[t][d] = model['month'][d]
                else:
                    if d == 'countries':
                        d0 = 'country'
                    elif d == 'dates':
                        d0 = 'date'
                    elif d == 'queries':
                        d0 = 'query'
                    for m_pos in range(len(model['month'][d])):
                        match = False
                        for t_pos in range(len(model[t][d])):
                            if model['month'][d][m_pos][d0] == model[t][d][t_pos][d0]:
                                match = True
                                model[t][d][t_pos]['times'] += model['month'][d][m_pos]['times']
                                if d == 'queries' and model[t][d][t_pos]['records'] != model['month'][d][m_pos]['records']:
                                    model[t][d][t_pos]['records'] = model['month'][d][m_pos]['records']
                                break
                        if match is False:
                            model[t][d].append(model['month'][d][m_pos])
    return model

            # for m_pos in range(len(model['month']['countries'])):
            #     match = False
            #     for t_pos in range(len(model[t]['countries'])):
            #         if model['month']['countries'][m_pos]['country'] == model[t]['countries'][t_pos]['country']:
            #             match = True
            #             model[t]['countries'][t_pos]['times'] += model['month']['countries'][m_pos]['times']
            #             break
            #     if match is False:
            #         model[t]['countries'].append(model['month']['countries'][m_pos])
            # for m_pos in range(len(model['month']['dates'])):
            #     match = False
            #     for t_pos in range(len(model[t]['dates'])):
            #         if model['month']['dates'][m_pos]['date'] == model[t]['dates'][t_pos]['date']:
            #             match = True
            #             model[t]['dates'][t_pos]['times'] += model['month']['dates'][m_pos]['times']
            #             break
            #     if match is False:
            #         model[t]['dates'].append(model['month']['dates'][m_pos])
            # model = json.loads(base64.b64decode(json.loads(r.content)['content']))['year']
            # old_history = json.loads(base64.b64decode(json.loads(r.content)['content']))['history']
            #
            # for t in ['year', 'history']:
            #     old = json.loads(base64.b64decode(json.loads(r.content)['content']))[t]
            #     if t not in model:  # Shouldn't be necessary, because if year is not present,
            #         model[t] = old  # it means there's nothing in last_month value, but JIC
            #     else:
            #         model[t]['downloads'] += old['downloads']
            #         model[t]['dowloads_period'] += old['dowloads_period']
            #         model[t]['records'] += old['records']
            #         model[t]['records_period'] += old['records_period']
            #
            #         if 'countries_list' not in model[t].keys():
            #             model[t]['countries_list'] = model['month']['countries_list']
            #         else:
            #             for c in model['month']['countries_list']:
            #                 if c not in
            # if 'history' not in model:
            #     model['history'] = old_history
            # else:
            #     model['history']['downloads'] += old_history['downloads']
            #     model['history']['dowloads_period'] += old_history['dowloads_period']
            #     model['history']['records'] += old_history['records']
            #     model['history']['records_period'] += old_history['records_period']

            # return model
        # else:
        #     return model


def addInitialYearToModel(model):
    """Add values for January 2014"""

    path = './reports_2014_01/{0}-{1}.json'.format(model['inst'], model['col'])
    try:
        d = json.loads(open(path, 'r').read().rstrip())
    except:
        return model

    if 'year' not in model:         # "Month" may sound confusing, but it's the name of the element containing
        model['year'] = d['month']  # year-round cumulative values

    else:                                       # Shouldn't apply because
        for i in d['month']:                    # this is only called if
            model['year'][i] += d['month'][i]   # there's no previous data

    return model


def addInitialHistoryToModel(model):
    """Add values for 2013 and add January 2014 values"""

    path = './reports_2013/{0}-{1}.json'.format(model['inst'], model['col'])
    try:
        d = json.loads(open(path, 'r').read().rstrip())
    except:
        return model

    if 'history' not in model:
        model['history'] = d['year']

        # Add 2014/01 values to history if present
        if 'year' in model:
            for i in model['history']:
                model['history'][i] += model['year'][i]

    else:                                        # Shouldn't apply because
        for i in d['year']:                      # this is only called if
            model['history'][i] += d['year'][i]  # there's no previous data

    return model


def createReport(model):
    """Create txt and html reports based on model values"""
    JINJA_ENVIRONMENT = jinja2.Environment(
        loader = jinja2.FileSystemLoader(os.path.dirname(__file__)),
        extensions = ['jinja2.ext.autoescape'],
        autoescape = True)

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
        'time_lapse': model['report_month_string'],
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


def main(pubs, lapse):

    logging.info('generating reports')
    created_at = format(datetime.now(), '%Y_%m_%d')
    reports = {}
    models = {}

    for pub in pubs:
        model = buildModel(pubs, pub, lapse)
        model = addPastDataToModel(model)

        report_txt, report_html = createReport(model)

        models[pub] = model
        reports[pub] = {'url': pubs[pub]['url'], 'inst': pubs[pub]['inst'], 'col': pubs[pub]['col'],
                        'created_at': created_at, 'content_txt': report_txt, 'content_html': report_html}

    return reports, models
