from util import sanity_check, cartodb_query
from datetime import datetime
from Model import Model

class ModelContainer():
    def __init__(self):
        self.models = {}
        return
    
    
    def parse_gso(self, gso):
        """Create or update models from a Google Cloud Storage object"""
        
        skipped_records = 0
        
        for rec in list(range(len(gso.records))):
            
            # Resource URL, which will act as ID
            this_url = gso.records[rec]._datasource_and_rights
            this_url = sanity_check(this_url)

            # Create empty model
            if this_url not in self.models.keys():
                this_model = Model()
                this_model.url = this_url
                
                # Extract resource metadata
                this_model.inst = self.fix_inst(gso.records[rec]._institutioncode)
                this_model.col = gso.records[rec]._collectioncode
                if this_model.inst == '' or this_model.col == '':
                    this_model.inst, this_model.col = self.get_inst_col(this_model.url)
                if this_model.inst is None or this_model.col is None:
                    print "Warning, inst and/or col missing"
                    print this_url, ":", this_model.inst, ":", this_model.col
                this_model.get_github_data()
                
                # Download event data
                this_model.month.records_downloaded = 1
            
            # Update existing model
            else:
                this_model = self.models[this_url]
                this_model.month.records_downloaded += 1
            
            # Add cumulative values
            
            # Add download file to list if not present
            if gso._download not in this_model.month._downloads_list:
                this_model.month._downloads_list.append(gso._download)
            
            # Add record to list of uniques if not present
            this_uuid = '/'.join([this_model.inst, this_model.col, gso.records[rec]._catalognumber])
            if this_uuid not in this_model.month._uuids:
                this_model.month._uuids.append(this_uuid)
            
            # Add this_model to dict of models
            self.models[this_url] = this_model
        
        # Update some cumulative counts
        for i in self.models.keys():
            self.models[i].month.downloads = len(self.models[i].month._downloads_list)
            self.models[i].month.unique_records_downloaded = len(self.models[i].month._uuids)
        
        return
    

    def parse_cdb(self, cdb):
        """Add data from CartoDB to model."""
        for model in self.models:
            pass
    
    
    def fix_inst(self, inst):
        """Fix certain cases where iname is used instead of icode"""
        
        if inst.startswith("Royal Ontario Museum"):
            fixed_inst = "ROM"
        elif inst.startswith('Borror Laboratory of Bioacoustics'):
            fixed_inst = 'BLB'
        elif inst.startswith('Ohio State University'):
            fixed_inst = 'OSUM'
        else:
            fixed_inst = inst
            
        return fixed_inst


    def get_inst_col(self, url):
        """Extract Institution code and Collection code from cartodb, using URL"""
        query = "select icode from resource_staging where url='{0}'".format(self.url)
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
