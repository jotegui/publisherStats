from datetime import datetime
from util import sanity_check, cartodb_query, get_org_repo
import logging

class Model():
    def __init__(self):
        
        # Initialize attributes
        
        # Resource metadata
        self.url = ""
        self.inst = ""
        self.col = ""
        self.github_org = ""
        self.github_repo = ""
        
        # Report metadata
        self.report_month = self.get_report_month()
        self.last_report_url = ""
        self.created_at = format(datetime.today(), "%Y/%m/%d")
        
        # Monthly data
        self.month = Month()
        
        # Cumulative data
        self.year = Year()
        self.history = History()
        
        return
        
    
    def get_report_month(self):
        pass
    
    
    def get_last_report_url(self, last_url_source):
        pass
    
    
    def get_github_data(self):
        """Use the get_org_repo function from util module to extract GitHub data from URL."""
        self.github_org, self.github_repo = get_org_repo(self.url)
        return


class Month():
    def __init__(self):
        
        # Downloads
        self._downloads_list = []
        self.downloads = None
        self.records_downloaded = None
        self._uuids = []
        self.unique_records_downloaded = None
        
        # Searches


class Year():
    def __init__(self):
        pass


class History():
    def __init__(self):
        pass
