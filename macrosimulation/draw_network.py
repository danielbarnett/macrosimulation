#!/usr/bin/python
# Filename: draw_network.py

import networkx as nx
import location_stuff as ls
from osgeo import gdal
from shapely.geometry import LineString, Point
from matplotlib.pyplot import figure, gca, axis, colorbar, imshow, quiver

def node_map(routeG, flow_thresh):
    # Draws a visual representation of the flow between nodes in the network
    el = list(e for e in routeG.edges(data=True) if e[2]['flow'] > flow_thresh)
    p = layout.random_layout(routeG)
    nx.draw_networkx(
        routeG, pos=dict((n, ls.transform_pt(n)) for n in routeG.nodes_iter()),
        edgelist = el, edge_color=list(e[2]['flow'] for e in el)
    )
    #draw_networkx_edge_labels(
    #    routeG,
    #    pos=dict((n, transform_pt(n)) for n in G.nodes_iter()), 
    #    edge_labels=dict(((u,v), '{0:.02}'.format(d['flow'])) for u, v, d in el)
    #)
    axis('equal');

from pyproj import Proj, transform

# Create the WGS84 (EPSG 4326) and BNG (EPSG 27700) projecions
WGS84 = Proj(init='epsg:4326')
BNG = Proj(init='epsg:27700')

# Iterate over each edge storing a LineString representation in the data
# dict with the "geom" key. Also add the length (in metres) to the dict as
# the "weight" key.
def make_geom_linestring(G):
    
    for n1, n2, data in G.edges_iter(data=True):
        # Convert n1 and n2 to the BNG
        p1, p2 = tuple(transform(WGS84, BNG, *n) for n in (n1, n2))
        
        # Create geometry
        lst = LineString((p1, p2))
        
        # Record in edge's data object
        data['geom'] = lst
        data['weight'] = lst.length
        
    return G

# Latitude and longitude of ROI's centre in degrees projected into BNG
# and the radus of the circle in metres. ROI lat/long taken from Wikipedia.
# NOTE: the order is longitude, latitude with WGS84
def create_subgraph(G, centre_long, centre_lat, radius):

    roi_centre, roi_radius = transform(WGS84, BNG, centre_long, centre_lat), radius
    
    # Create the ROI as a point buffered out to the ROI radius
    roi = Point(*roi_centre).buffer(roi_radius)
    
    nodes_of_interest = set()
    for n1, n2, data in G.edges_iter(data=True):
        if data['geom'].intersects(roi):
            nodes_of_interest.add(n1)
            nodes_of_interest.add(n2)
            
    subG = G.subgraph(nodes_of_interest)
    
    return subG

def plot_coords(ax, ob):
    x, y = ob.xy
    ax.plot(x, y, 'o', color='#999999', zorder=1)

def plot_bounds(ax, ob):
    x, y = zip(*list((p.x, p.y) for p in ob.boundary))
    ax.plot(x, y, 'o', color='#000000', zorder=1)

def plot_line(ax, ob):
    x, y = ob.xy
    ax.plot(x, y, color='r', alpha=0.9, linewidth=3, solid_capstyle='round', zorder=2)
    
def dsshow(ds, **kwargs):
    """Use imshow to shopw the GDAL dataset on a plot setting the
    extent of the image to match the extent of the dataset. Pass any keyword
    args on to imshow."""
    arr = ds.ReadAsArray()
    trans = ds.GetGeoTransform()
    extent = (trans[0], trans[0] + ds.RasterXSize*trans[1],
              trans[3] + ds.RasterYSize*trans[5], trans[3])

    imshow(arr[:3,:,:].transpose((1, 2, 0)), extent=extent, **kwargs)

from networkx import draw_networkx, draw_networkx_edges
import numpy as np

def draw_submap(image_file, line_shift, subG, centre_long, centre_lat, radius, interest_key):

    basemap_ds = gdal.Open(image_file)
    
    WGS84 = Proj(init='epsg:4326')
    BNG = Proj(init='epsg:27700')    
    
    # The magic args to quiver to make it behave like you'd hope
    quiver_args = dict(scale_units='xy', angles='xy', scale=1)
        
    # Convert our edges to a set of start x, y positions, deltas and values of interest.
    # Shift the position to the left by "shift_amount".
    quiver_data = []
    shift_amount = line_shift # metres
    key_of_interest = interest_key
    for _, _, data in subG.edges_iter(data=True):
        lst = data['geom']
        lxs, lys = lst.xy
        delta = np.array((lxs[-1]-lxs[0], lys[-1]-lys[0]))
        norm_delta = delta / np.linalg.norm(delta)
        v = data[key_of_interest]
            
        quiver_data.append(([
            lxs[0] - shift_amount * norm_delta[1],
            lys[0] + shift_amount * norm_delta[0],
            lxs[-1]-lxs[0], lys[-1]-lys[0],
            v
        ]))
    
    quiver_data = np.array(quiver_data)
    
    f = figure()
    ax = f.add_subplot(1, 1, 1, axisbg='black')
    
    dsshow(basemap_ds, alpha=0.25)
    
    # Show the "good values"
    qv = quiver(quiver_data[:,0], quiver_data[:,1],
           quiver_data[:,2], quiver_data[:,3],
           quiver_data[:,4], cmap='hot', **quiver_args)
    
    # Show the missing values in a bright color so we won't miss them.
    mv = np.isnan(quiver_data[:,4])
    quiver(quiver_data[mv,0], quiver_data[mv,1],
           quiver_data[mv,2], quiver_data[mv,3],
           color=(0.0, 1.0, 0.0), **quiver_args)
    
    roi_centre, roi_radius = transform(WGS84, BNG, centre_long, centre_lat), radius
        
    # Create the ROI as a point buffered out to the ROI radius
    roi = Point(*roi_centre).buffer(roi_radius)
    
    plot_line(gca(), roi.exterior)
    
    # Set axes to zoom into ROI with some padding
    pad = 5e3 # metres
    axis((roi.bounds[0]-pad, roi.bounds[2]+pad, roi.bounds[1]-pad, roi.bounds[3]+pad))
    
    # Add a colorbar
    cb = colorbar(qv)
    cb.set_label(key_of_interest)

