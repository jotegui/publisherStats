class RecordLengthError(Exception):
    def __init__(self,value):
        self.value=value
    def __str__(self):
        return repr(self.value)


class Record():
    def __init__(self, line):
        
        # List of DwC fields
        self._fieldList = ["datasource_and_rights", "type", "modified", "language", "rights", "rightsholder", "accessrights", "bibliographiccitation", "references", "institutionid", "collectionid", "datasetid", "institutioncode", "collectioncode", "datasetname", "ownerinstitutioncode", "basisofrecord", "informationwithheld", "datageneralizations", "dynamicproperties", "occurrenceid", "catalognumber", "occurrenceremarks", "recordnumber", "recordedby", "individualid", "individualcount", "sex", "lifestage", "reproductivecondition", "behavior", "establishmentmeans", "occurrencestatus", "preparations", "disposition", "othercatalognumbers", "previousidentifications", "associatedmedia", "associatedreferences", "associatedoccurrences", "associatedsequences", "associatedtaxa", "eventid", "samplingprotocol", "samplingeffort", "eventdate", "eventtime", "startdayofyear", "enddayofyear", "year", "month", "day", "verbatimeventdate", "habitat", "fieldnumber", "fieldnotes", "eventremarks", "locationid", "highergeographyid", "highergeography", "continent", "waterbody", "islandgroup", "island", "country", "countrycode", "stateprovince", "county", "municipality", "locality", "verbatimlocality", "verbatimelevation", "minimumelevationinmeters", "maximumelevationinmeters", "verbatimdepth", "minimumdepthinmeters", "maximumdepthinmeters", "minimumdistanceabovesurfaceinmeters", "maximumdistanceabovesurfaceinmeters", "locationaccordingto", "locationremarks", "verbatimcoordinates", "verbatimlatitude", "verbatimlongitude", "verbatimcoordinatesystem", "verbatimsrs", "decimallatitude", "decimallongitude", "geodeticdatum", "coordinateuncertaintyinmeters", "coordinateprecision", "pointradiusspatialfit", "footprintwkt", "footprintsrs", "footprintspatialfit", "georeferencedby", "georeferenceddate", "georeferenceprotocol", "georeferencesources", "georeferenceverificationstatus", "georeferenceremarks", "geologicalcontextid", "earliesteonorlowesteonothem", "latesteonorhighesteonothem", "earliesteraorlowesterathem", "latesteraorhighesterathem", "earliestperiodorlowestsystem", "latestperiodorhighestsystem", "earliestepochorlowestseries", "latestepochorhighestseries", "earliestageorloweststage", "latestageorhigheststage", "lowestbiostratigraphiczone", "highestbiostratigraphiczone", "lithostratigraphicterms", "group", "formation", "member", "bed", "identificationid", "identifiedby", "dateidentified", "identificationreferences", "identificationverificationstatus", "identificationremarks", "identificationqualifier", "typestatus", "taxonid", "scientificnameid", "acceptednameusageid", "parentnameusageid", "originalnameusageid", "nameaccordingtoid", "namepublishedinid", "taxonconceptid", "scientificname", "acceptednameusage", "parentnameusage", "originalnameusage", "nameaccordingto", "namepublishedin", "namepublishedinyear", "higherclassification", "kingdom", "phylum", "class", "order", "family", "genus", "subgenus", "specificepithet", "infraspecificepithet", "taxonrank", "verbatimtaxonrank", "scientificnameauthorship", "vernacularname", "nomenclaturalcode", "taxonomicstatus", "nomenclaturalstatus", "taxonremarks"]
        
        # Build each attribute with content of GCS object
        self._datasource_and_rights = None
        self._type = None
        self._modified = None
        self._language = None
        self._rights = None
        self._rightsholder = None
        self._accessrights = None
        self._bibliographiccitation = None
        self._references = None
        self._institutionid = None
        self._collectionid = None
        self._datasetid = None
        self._institutioncode = None
        self._collectioncode = None
        self._datasetname = None
        self._ownerinstitutioncode = None
        self._basisofrecord = None
        self._informationwithheld = None
        self._datageneralizations = None
        self._dynamicproperties = None
        self._occurrenceid = None
        self._catalognumber = None
        self._occurrenceremarks = None
        self._recordnumber = None
        self._recordedby = None
        self._individualid = None
        self._individualcount = None
        self._sex = None
        self._lifestage = None
        self._reproductivecondition = None
        self._behavior = None
        self._establishmentmeans = None
        self._occurrencestatus = None
        self._preparations = None
        self._disposition = None
        self._othercatalognumbers = None
        self._previousidentifications = None
        self._associatedmedia = None
        self._associatedreferences = None
        self._associatedoccurrences = None
        self._associatedsequences = None
        self._associatedtaxa = None
        self._eventid = None
        self._samplingprotocol = None
        self._samplingeffort = None
        self._eventdate = None
        self._eventtime = None
        self._startdayofyear = None
        self._enddayofyear = None
        self._year = None
        self._month = None
        self._day = None
        self._verbatimeventdate = None
        self._habitat = None
        self._fieldnumber = None
        self._fieldnotes = None
        self._eventremarks = None
        self._locationid = None
        self._highergeographyid = None
        self._highergeography = None
        self._continent = None
        self._waterbody = None
        self._islandgroup = None
        self._island = None
        self._country = None
        self._countrycode = None
        self._stateprovince = None
        self._county = None
        self._municipality = None
        self._locality = None
        self._verbatimlocality = None
        self._verbatimelevation = None
        self._minimumelevationinmeters = None
        self._maximumelevationinmeters = None
        self._verbatimdepth = None
        self._minimumdepthinmeters = None
        self._maximumdepthinmeters = None
        self._minimumdistanceabovesurfaceinmeters = None
        self._maximumdistanceabovesurfaceinmeters = None
        self._locationaccordingto = None
        self._locationremarks = None
        self._verbatimcoordinates = None
        self._verbatimlatitude = None
        self._verbatimlongitude = None
        self._verbatimcoordinatesystem = None
        self._verbatimsrs = None
        self._decimallatitude = None
        self._decimallongitude = None
        self._geodeticdatum = None
        self._coordinateuncertaintyinmeters = None
        self._coordinateprecision = None
        self._pointradiusspatialfit = None
        self._footprintwkt = None
        self._footprintsrs = None
        self._footprintspatialfit = None
        self._georeferencedby = None
        self._georeferenceddate = None
        self._georeferenceprotocol = None
        self._georeferencesources = None
        self._georeferenceverificationstatus = None
        self._georeferenceremarks = None
        self._geologicalcontextid = None
        self._earliesteonorlowesteonothem = None
        self._latesteonorhighesteonothem = None
        self._earliesteraorlowesterathem = None
        self._latesteraorhighesterathem = None
        self._earliestperiodorlowestsystem = None
        self._latestperiodorhighestsystem = None
        self._earliestepochorlowestseries = None
        self._latestepochorhighestseries = None
        self._earliestageorloweststage = None
        self._latestageorhigheststage = None
        self._lowestbiostratigraphiczone = None
        self._highestbiostratigraphiczone = None
        self._lithostratigraphicterms = None
        self._group = None
        self._formation = None
        self._member = None
        self._bed = None
        self._identificationid = None
        self._identifiedby = None
        self._dateidentified = None
        self._identificationreferences = None
        self._identificationverificationstatus = None
        self._identificationremarks = None
        self._identificationqualifier = None
        self._typestatus = None
        self._taxonid = None
        self._scientificnameid = None
        self._acceptednameusageid = None
        self._parentnameusageid = None
        self._originalnameusageid = None
        self._nameaccordingtoid = None
        self._namepublishedinid = None
        self._taxonconceptid = None
        self._scientificname = None
        self._acceptednameusage = None
        self._parentnameusage = None
        self._originalnameusage = None
        self._nameaccordingto = None
        self._namepublishedin = None
        self._namepublishedinyear = None
        self._higherclassification = None
        self._kingdom = None
        self._phylum = None
        self._class = None
        self._order = None
        self._family = None
        self._genus = None
        self._subgenus = None
        self._specificepithet = None
        self._infraspecificepithet = None
        self._taxonrank = None
        self._verbatimtaxonrank = None
        self._scientificnameauthorship = None
        self._vernacularname = None
        self._nomenclaturalcode = None
        self._taxonomicstatus = None
        self._nomenclaturalstatus = None
        self._taxonremarks = None
        
        # Build attributes
        self.process_line(line)
        
        return
    
    
    def process_line(self, line):
        
        # Check if line has 160 fields
        if len(line) != 160:
            raise RecordLengthError("Record has {0} fields. Should be 160.".format(len(line)))
        
        # Store each value in its corresponding attribute
        for term_pos in list(range(len(self._fieldList))):
            
            # Extract term from list and value from line
            term = self._fieldList[term_pos]
            value = line[term_pos]
            
            # Set value for attribute
            setattr(self, "_"+term, value)
        
        return
