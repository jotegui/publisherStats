import os
import json
import base64
import jinja2
#import urllib2
import logging
import requests
from datetime import datetime
from util import get_org_repo, geonames_query


def unescape(s):
    """Replace encoded characters"""
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    s = s.replace("&#34;", "\"")
    # Add more as they appear
    s = s.replace("&amp;", "&")
    return s


def get_time_lapse(today, lapse='month'):
    """Build "February, 2014" and "2014/02" strings for the specified month"""
    if lapse == 'full':
        report_month_string = 'ever since February, 2014'
        report_month = '2014/02'
    else:
        this_year = today.year
        this_month = today.month
        if this_month == 1:
            report_month_string = '{0}'.format(datetime(this_year - 1, 12, 1).strftime('%B, %Y'))
            report_month = '{0}'.format(datetime(this_year - 1, 12, 1).strftime('%Y/%m'))
        else:
            report_month_string = '{0}'.format(datetime(this_year, this_month - 1, 1).strftime('%B, %Y'))
            report_month = '{0}'.format(datetime(this_year, this_month - 1, 1).strftime('%Y/%m'))
    return report_month_string, report_month


def find_last_report(inst, col, today):
    """Check if there is a previous report for the resource"""
    pub = '-'.join([inst, col])
    try:
        models = json.loads(open('./modelURLs.json', 'r').read().rstrip())[pub]  # TODO: Update with final location
        last_url = models[-1]
        last_report_month = get_time_lapse(datetime.strptime(get_time_lapse(today=today)[1], '%Y/%m'))[1]
        if last_url.endswith('{0}_{1}.json'.format(last_report_month.split('/')[0], last_report_month.split('/')[1])):
            pass
        else:
            last_url = ''
    except:
        last_url = ''
    return last_url


def build_model(pubs, pub, lapse, today):
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
        "downloads": {  # Monthly values for downloads
            "downloads": 0,
            "downloads_period": 0,
            "records": 0,
            "records_period": 0,
            "records_unique": 0,
            "countries_list": [],
            "countries": [],
            "dates": [],
            "queries": []
        },
        "searches": {  # Monthly values for searches
            "searches": 0,
            "records": 0,
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

    report_month_string, report_month = get_time_lapse(today=today, lapse=lapse)
    model['report_month_string'] = report_month_string
    model['report_month'] = report_month

    model['last_report_url'] = find_last_report(inst, col, today)

    created_at = format(today, '%Y/%m/%d')
    model['created_at'] = created_at

    # DOWNLOADS
    try:  # Try adding download values
        downloads = len(pubs[pub]['download_files'])
        model['downloads']['downloads'] = downloads
        total_downloads = pubs[pub]['downloads_in_period']
        model['downloads']['downloads_period'] = total_downloads
        records = pubs[pub]['records_downloaded']
        model['downloads']['records'] = records
        total_records = pubs[pub]['tot_recs']
        model['downloads']['records_period'] = total_records
        unique_records = len(pubs[pub]['unique_records'])
        model['downloads']['records_unique'] = unique_records

        countries = {}
        for i in pubs[pub]['latlon']:
            lat = i[0]
            lon = i[1]
            country = geonames_query(lat, lon)
            if country not in countries:
                countries[country] = pubs[pub]['latlon'][i]
            else:
                countries[country] += pubs[pub]['latlon'][i]
        or_countries = countries.keys()
        or_countries.sort()
        for i in or_countries:
            model['downloads']['countries_list'].append(i)
            model['downloads']['countries'].append({"country": i, "times": countries[i]})

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
            model['downloads']['dates'].append({"date": i, "times": query_dates[i]})

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
            model['downloads']['queries'].append({"query": i, "times": queries[i][0], "records": queries[i][1]})

    except KeyError:  # If fails, it means there have been no downloads in the period, so use default values
        pass

    # SEARCHES

    try:  # Try adding download values
        searches = pubs[pub]['searches']['searches']
        model['searches']['searches'] = searches
        records = pubs[pub]['searches']['records_searched']
        model['searches']['records'] = records

        countries = {}
        for i in pubs[pub]['searches']['latlon']:
            lat = i[0]
            lon = i[1]
            country = geonames_query(lat, lon)
            if country not in countries:
                countries[country] = pubs[pub]['searches']['latlon'][i]
            else:
                countries[country] += pubs[pub]['searches']['latlon'][i]
        or_countries = countries.keys()
        or_countries.sort()
        for i in or_countries:
            model['searches']['countries_list'].append(i)
            model['searches']['countries'].append({"country": i, "times": countries[i]})

        query_dates = {}
        for i in pubs[pub]['searches']['created']:
            this_date = i
            this_times = pubs[pub]['searches']['created'][i]
            if this_date not in query_dates:
                query_dates[this_date] = this_times
            else:
                query_dates[this_date] += this_times
        or_query_dates = query_dates.keys()
        or_query_dates.sort()
        for i in or_query_dates:
            model['searches']['dates'].append({"date": i, "times": query_dates[i]})

        queries = {}
        for i in pubs[pub]['searches']['query']:
            this_query = i
            this_values = pubs[pub]['searches']['query'][i]
            this_times = this_values[0]
            this_records = this_values[1]
            if this_query not in queries:
                queries[this_query] = [this_times, this_records]
            else:
                queries[this_query][0] += this_times
        for i in queries:
            model['searches']['queries'].append({"query": i, "times": queries[i][0], "records": queries[i][1]})

    except KeyError:  # If fails, it means there have been no searches in the period, so use default values
        pass

    return model


def load_previous_model(model):
    # If it's the first time, take 2013 and 2014/01 values from files
    if model['last_report_url'] == "":
        model = add_initial_year(model)
        model = add_initial_history(model)

    # Else, take values from last month's json
    else:

        url = model['last_report_url']
        r = requests.get(url)

        if r.status_code == 200:

            prev_model = json.loads(base64.b64decode(json.loads(r.content)['content']))
            model['year'] = prev_model['year']
            model['history'] = prev_model['history']

    return model


def add_history_year_data(model, t):

    # If report for first month of year, reset year counts to monthly values
    if t == 'year' and model['report_month'][-2:] == '01':
        for i in model['downloads']:
            model[t][i] = model['downloads'][i]
    else:
        # Add basic counts
        if 'downloads' in model[t]:
            model[t]['downloads'] += model['downloads']['downloads']
        else:
            model[t]['downloads'] = model['downloads']['downloads']
        if 'downloads_period' in model[t]:
            model[t]['downloads_period'] += model['downloads']['downloads_period']
        else:
            model[t]['downloads_period'] = model['downloads']['downloads_period']
        if 'records' in model[t]:
            model[t]['records'] += model['downloads']['records']
        else:
            model[t]['records'] = model['downloads']['records']
        if 'records_period' in model[t]:
            model[t]['records_period'] += model['downloads']['records_period']
        else:
            model[t]['records_period'] = model['downloads']['records_period']

        # Append any non-existing country to list
        if 'countries_list' in model[t]:
            for c in model['downloads']['countries_list']:
                if c not in model[t]['countries_list']:
                    model[t]['countries_list'].append(c)
        else:
            model[t]['countries_list'] = model['downloads']['countries_list']

        # Add Countries and Dates counts. Same for Queries, but if record count is modified, update it
        for d in ['countries', 'dates', 'queries']:
            if d not in model[t]:
                model[t][d] = model['downloads'][d]
            else:
                if d == 'countries':
                    d0 = 'country'
                elif d == 'dates':
                    d0 = 'date'
                elif d == 'queries':
                    d0 = 'query'
                for m_pos in range(len(model['downloads'][d])):
                    match = False
                    for t_pos in range(len(model[t][d])):
                        if model['downloads'][d][m_pos][d0] == model[t][d][t_pos][d0]:
                            match = True
                            model[t][d][t_pos]['times'] += model['downloads'][d][m_pos]['times']
                            if d == 'queries' and model[t][d][t_pos]['records'] != model['downloads'][d][m_pos]['records']:
                                model[t][d][t_pos]['records'] = model['downloads'][d][m_pos]['records']
                            break
                    if match is False:
                        model[t][d].append(model['downloads'][d][m_pos])

    return model


def add_past_data(model):
    """Add year and history cumulative values"""

    # First, put the previous month's year and history objects in the month model
    model = load_previous_model(model)

    # Now, add monthly values to history and to year if still in same year
    for t in ['history', 'year']:
        model = add_history_year_data(model, t)

    return model


def add_initial_year(model):
    """Add values for January 2014"""

    path = './reports_2014_01/{0}-{1}.json'.format(model['inst'], model['col'])
    try:
        d = json.loads(open(path, 'r').read().rstrip())
    except IOError:
        model['year'] = {"downloads": 0, "records": 0}
        return model

    if 'year' not in model:         # "Month" may sound confusing, but it's the name of the element containing
        model['year'] = d['month']  # year-round cumulative values

    else:                                       # Shouldn't apply because
        for i in d['month']:                    # this is only called if
            model['year'][i] += d['month'][i]   # there's no previous data

    return model


def add_initial_history(model):
    """Add values for 2013 and add January 2014 values"""

    path = './reports_2013/{0}-{1}.json'.format(model['inst'], model['col'])
    try:
        d = json.loads(open(path, 'r').read().rstrip())
    except IOError:
        model['history'] = {"downloads": 0, "records": 0}
        return model

    if 'history' not in model:
        model['history'] = d['year']

        # Add 2014/01 values to history if present
        if 'year' in model:
            model['history']['downloads'] += model['year']['downloads']
            model['history']['records'] += model['year']['records']

    else:                                        # Shouldn't apply because
        for i in d['year']:                      # this is only called if
            model['history'][i] += d['year'][i]  # there's no previous data

    return model


def countries_dates_queries(model, t):

    if t != 'downloads' and t != 'searches':
        return
    else:
        t_countries = []
        countries = model[t]['countries']
        for i in countries:
            t_countries.append([i['country'], i['times']])

        t_dates = []
        dates = model[t]['dates']
        for i in dates:
            t_dates.append([i['date'], i['times']])

        t_queries = {}
        queries = model[t]['queries']
        for i in queries:
            if i['query'] not in t_queries:
                t_queries[i['query']] = i['times']

        return t_countries, t_dates, t_queries


def create_report(model):
    """Create txt and html reports based on model values"""
    jinja_environment = jinja2.Environment(
        loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
        extensions=['jinja2.ext.autoescape'],
        autoescape=True)

    q_countries, q_dates, q_queries = countries_dates_queries(model, 'downloads')
    s_countries, s_dates, s_queries = countries_dates_queries(model, 'searches')

    try:
        m_year_downloads = model['year']['downloads']
        m_year_records = model['year']['records']
    except KeyError:
        m_year_downloads = 'No data'
        m_year_records = 'No data'
    try:
        m_hist_downloads = model['history']['downloads']
        m_hist_records = model['history']['records']
    except KeyError:
        m_hist_downloads = 'No data'
        m_hist_records = 'No data'

    template_values = {
        # General values
        'inst': model['inst'],
        'resname': model['col'],
        'time_lapse': model['report_month_string'],
        'generated': model['created_at'],
        # Downloads
        'downloads': model['downloads']['downloads'],
        'total_downloads': model['downloads']['downloads_period'],
        'records': model['downloads']['records'],
        'total_records': model['downloads']['records_period'],
        'unique_records': model['downloads']['records_unique'],
        'len_countries': len(model['downloads']['countries_list']),
        'countries': q_countries,
        'query_dates': q_dates,
        'queries': q_queries,
        # Searches
        'searches': model['searches']['searches'],
        'records_searched': model['searches']['records'],
        's_len_countries': len(model['searches']['countries_list']),
        's_countries': s_countries,
        's_query_dates': s_dates,
        's_queries': s_queries,
        # Cumulative data
        'year_downloads': m_year_downloads,
        'year_records': m_year_records,
        'history_downloads': m_hist_downloads,
        'history_records': m_hist_records
    }

    template_txt = jinja_environment.get_template('template.txt')
    report_txt = unescape(template_txt.render(template_values))
    template_html = jinja_environment.get_template('template.html')
    report_html = template_html.render(template_values)

    return report_txt, report_html


def add_org_repo(models):
    """Populate the org and repo fields in the model"""
    for i in models:
        org, repo = get_org_repo(models[i]['url'])
        if org is not None and repo is not None:
            models[i]['github_org'] = org
            models[i]['github_repo'] = repo
    return models


def main(pubs, lapse, today):

    logging.info('generating reports')
    created_at = format(today, '%Y_%m_%d')
    reports = {}
    models = {}

    for pub in pubs:
        model = build_model(pubs, pub, lapse, today)
        model = add_past_data(model)

        report_txt, report_html = create_report(model)

        models[pub] = model
        reports[pub] = {'url': pubs[pub]['url'], 'inst': pubs[pub]['inst'], 'col': pubs[pub]['col'],
                        'created_at': created_at, 'content_txt': report_txt, 'content_html': report_html}

    # Add org and repo to models
    models = add_org_repo(models)

    return reports, models
