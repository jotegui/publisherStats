from datetime import datetime

class CartoDBObject():
    def __init__(self, json_string):
        self.type = json_string['type']
        self.created_at = datetime.strptime(json_string['created_at'], '%Y-%m-%dT%H:%M:%SZ')
        self.lat = float(json_string['lat'])
        self.lon = float(json_string['lon'])
        self.download = json_string['download']
        self.query = json_string['query']
        self.results_by_resource = json_string['results_by_resource']  # Parse this

