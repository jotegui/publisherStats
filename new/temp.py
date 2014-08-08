import json
import urllib2
from datetime import datetime


class downloader():
    def __init__(self):
        self.today = datetime.today()
        return
    
    def api_query(self, api_url, params, res_field):
        """Launch query to an API with the specified query and retrieve the specified field."""
        query_url = '?'.join([api_url, urlencode(params)])
        max_retries = 5
        retry = 0
        while retry < max_retries:
            try:
                d = json.loads(urllib2.urlopen(query_url).read())[res_field]
                return d
            except urllib2.HTTPError:
                retry += 1
        return []


    def cartodb_query(self, query):
        """Build parameters for launching a query to the CartoDB API."""
        api_url = 'https://vertnet.cartodb.com/api/v2/sql'
        params = {'q': query}
        res_field = 'rows'
        d = self.api_query(api_url=api_url, params=params, res_field=res_field)
        return d


    def geonames_query(self, lat, lon):
        """Build parameters for launching a query to the GeoNames API."""
        api_url = 'http://api.geonames.org/countryCodeJSON'
        params = {
            'formatted': 'true',
            'lat': lat,
            'lng': lon,
            'username': 'jotegui',
            'style': 'full'
        }
        res_field = 'countryName'
        d = self.api_query(api_url=api_url, params=params, res_field=res_field)
        return d
    
    def add_time_limit(self, query, today, lapse='month'):
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
    
    def get_cdb_downloads(self, lapse, today):
        """Download the info in the downloads from CDB"""

        query = "select * from query_log where download is not null and download !=''"
        query += " and client='portal-prod'"  # Just production portal downloads

        query = self.add_time_limit(query=query, today=today, lapse=lapse)  # Just from the specific month

        d = self.cartodb_query(query)
        return d
