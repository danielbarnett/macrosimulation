#!/usr/bin/python
# Filename: get_latest_data.py

"""
Imports traffic data and puts it into arrays, depending on what is asked for - it can produce location, flow, 
occupancy or speed data.
"""

import lxml.objectify as lo
from urllib2 import urlopen
import check_internet

def create_data_array(data_type):

    PREDEFINED_LOCATIONS_DOCUMENT_URL = \
    'http://hatrafficinfo.dft.gov.uk/feeds/datex/England/PredefinedLocation/content.xml'
    TRAFFIC_DATA_DOCUMENT_URL = 'http://hatrafficinfo.dft.gov.uk/feeds/datex/England/TrafficData/content.xml'
    
    if data_type == 'flow':
        value1 = 'TrafficFlow'
        value2 = 'vehicleFlow'
    elif data_type == 'occupancy':
        value1 = 'TrafficConcentration'
        value2 = data_type
    elif data_type == 'speed':
        value1 = 'TrafficSpeed'
        value2 = 'averageVehicleSpeed'
    
    if data_type == 'location':
        links_root = lo.parse(urlopen(PREDEFINED_LOCATIONS_DOCUMENT_URL)).getroot()
	print "Location data downloaded. Beginning processing..."
        data_set = links_root.payloadPublication.predefinedLocationSet.predefinedLocation
    elif data_type == 'flow' or data_type == 'occupancy' or data_type == 'speed':
        traffic_root = lo.parse(urlopen(TRAFFIC_DATA_DOCUMENT_URL)).getroot()
	print "Data downloaded. Beginning processing..."
        traffic_set = traffic_root.payloadPublication.elaboratedData
        data_set = []
        for elab in traffic_set:
            if elab.basicDataValue.attrib == {'{http://www.w3.org/2001/XMLSchema-instance}type': value1}:
                if hasattr(elab.basicDataValue, value2): 
                    thing = getattr(elab.basicDataValue, value2)
                    data_set.append((elab.basicDataValue.affectedLocation.locationContainedInGroup.predefinedLocationReference, \
                           thing))
        
    return data_set

