from urllib import urlencode
import urllib2

from Record import Record

class MissingArchiveError(Exception):
    def __init__(self,value):
        self.value=value
    def __str__(self):
        return repr(self.value)

class GoogleStorageObject():
    
    def __init__(self, bucket_name, object_name):
        """Initialize the download and parsing of the GoogleStorageObject from Google Storage API"""
        
        # Identification of the object
        self._bucket_name = bucket_name
        self._object_name = object_name
        self._download = "/".join(["", "gs", self._bucket_name, self._object_name])
        
        # Base URL for Google Storage API
        self._gcs_url = 'https://www.googleapis.com/storage/v1'
        
        # Container for Record objects
        self.records = []
        
        # Download object from Google Cloud Storage
        raw = self.download_object(bucket_name, object_name)
        
        # Parse downloaded object
        self.parse_object(raw)
        
        return
    
    
    @classmethod
    def fromuri(cls, uri):
        """Create GoogleStorageObject from URI instead of bucket and object names"""
        sl = uri.split("/")
        b = sl[2]
        o = sl[3]
        return cls(b, o)
    
    
    def download_object(self, bucket_name, object_name):
        """Get raw content of object in bucket"""

        # Build API url
        url = '/'.join([self._gcs_url, 'b', bucket_name, 'o', object_name.replace(' ', '%20')])
        url_optim = '?'.join([url, urlencode({'alt': 'media'})])

        # Download object
        try:
            raw = urllib2.urlopen(url_optim).read()
        except urllib2.HTTPError as e:
            raise MissingArchiveError("File {0} not found in bucket {1}".format(object_name, bucket_name))
        
        return raw
    
    
    def parse_object(self, raw):
        """Parse downloaded object to object type, and create individual Record objects"""
        
        # Make array of lines
        lines = raw.split("\n")
        
        # If last line is just "\n", remove last line
        if len(lines[-1]) <= 1:
            lines = lines[:-1]
        # Remove headers if present
        if lines[0].split("\t")[0] == "datasource_and_rights":
            lines = lines[1:]
        
        # Count
        pos = 0

        # Process lines
        while pos < len(lines):
            splitline = lines[pos].split("\t")

            # Regular line
            if len(splitline) == 160:
                self.records.append(Record(splitline))

            # Two records in one line
            elif len(splitline) == 319:
                line1 = splitline[:159]
                line1.append("")
                self.records.append(Record(line1))
                line2 = splitline[159:]
                self.records.append(Record(line2))

            # One record in two lines
            elif len(splitline) < 160 and len(splitline) + len(lines[pos + 1].split("\t")) == 161:
                self.records.append(Record(lines[pos].split("\t")[:-1] + lines[pos + 1].split("\t")))
                pos += 1

            # Two records in three lines
            elif len(splitline) < 160 and len(splitline) + len(lines[pos + 1].split("\t")) > 161:
                line1 = splitline[:-1] + lines[pos + 1].split("\t")[:(160 - len(splitline))]
                line1.append("")
                self.records.append(Record(line1))
                line2 = lines[pos + 1].split("\t")[(160 - len(splitline)):-1] + lines[pos + 2].split("\t")
                self.records.append(Record(line2))
                pos += 2

            pos += 1
        
        return
