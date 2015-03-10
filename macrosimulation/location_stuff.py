#!/usr/bin/python
# Filename: location_stuff.py

import pyproj

def loc_to_to_from_long_lat(loc):
    '''Returns the longitude and latitude of the "to" and \
    "from" points of a location'''
    
    # goes to the "to" and "from" attributes of the element
    to_ = loc.predefinedLocation.tpeglinearLocation.to
    from_ = loc.predefinedLocation.tpeglinearLocation['from']
    
    # gets their coordinates and converts to floats
    to_latlng = (float(to_.pointCoordinates.longitude), float(to_.pointCoordinates.latitude))
    from_latlng = (float(from_.pointCoordinates.longitude), float(from_.pointCoordinates.latitude))
    
    # returns values
    return to_latlng, from_latlng

def loc_to_loc_id(loc):
    loc_id = str(loc.attrib).split()[1]
    loc_id = loc_id[1:len(loc_id)-2]
    return loc_id

#wgs84 = pyproj.Proj(init='epsg:4326')
#dst_proj = pyproj.Proj(init='epsg:3857')
#end_proj = pyproj.Proj(init='epsg:27700')

def transform_pt(pt, input_proj_code=4326, output_proj_code=27700):
    '''Transform points from wgs84 coordinates to Google Maps coordinates'''
    
    input_proj = pyproj.Prog(init='epsg:'+input_proj_code)
    output_proj = pyproj.Prog(init='epsg:'+output_proj_code)
    
    return pyproj.transform(input_proj, output_proj, pt[0], pt[1])

def transform_line(ln, input_proj_code=4326, output_proj_code=27700):
    '''Transform lines from wgs84 coordinates to Google Maps coordinates'''
    
    return tuple(transform_pt(p, input_proj_code, output_proj_code) for p in ln)

def find_flow_for_loc(loc, flows, missing_flow = 0):
    '''Returns the flow for a given location by using the indexing in "flows"'''
    
    # determines the location id of the given location
    loc_id = loc_to_loc_id(loc)
    
    # finds the matching index in the speeds list
    match = 0
    for flw in flows:
        if flw[0]==loc_id:
            match = flw[1]
        
    # returns the corresponding speed
    if match==0:
        return missing_flow
    else:
        return float(match)
    
def find_flow_for_long_lat(longlatlonglat, line_flows, missing_flow = 0):
    '''Finds a speed for a section of road defined by its coordinates'''
    
    match = 0
    for l in line_flows:
        if str(l[0])==str(longlatlonglat):
            match = l[2]
            
    if match==0:
        return missing_flow
    else:
        return float(match)

from shapely.geometry import Point, LineString

def localise_map(locs_set, centre_long, centre_lat, radius):

    roi_centre, roi_radius = (centre_long, centre_lat), radius
    
    # Create the ROI as a point buffered out to the ROI radius
    roi = Point(*roi_centre).buffer(roi_radius)
    
    roads = []
    for loc in locs_set:
        location = LineString([(loc.predefinedLocation.tpeglinearLocation.to.pointCoordinates.longitude, \
                     loc.predefinedLocation.tpeglinearLocation.to.pointCoordinates.latitude), \
                    (loc.predefinedLocation.tpeglinearLocation['from'].pointCoordinates.longitude, \
                     loc.predefinedLocation.tpeglinearLocation['from'].pointCoordinates.latitude)])
        if location.intersects(roi):
            roads.append(loc)
            
    return roads
