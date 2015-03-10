#!/usr/bin/python
# Filename: create_network.py>

import location_stuff as ls
import networkx as nx
import numpy as np

def nodes(roads, flows):
    
    line_flows = list((ls.loc_to_to_from_long_lat(loc), ls.loc_to_loc_id(loc), \
                   ls.find_flow_for_loc(loc, flows)) for loc in roads)

    in_nodes = list(tuple(l[0][0]) for l in line_flows)
    out_nodes = list(tuple(l[0][1]) for l in line_flows)
    
    return in_nodes, out_nodes

def edges_from_nodes(in_nodes, out_nodes):
    
    edges = list(edge for edge in zip(in_nodes, out_nodes))
    
    return edges

def create_digraph(edges, flows, roads, flow, occupancy=False, speed=False):
    
    G = nx.DiGraph()
    G.add_edges_from(edges)

    line_flows = list((ls.loc_to_to_from_long_lat(loc), ls.loc_to_loc_id(loc), \
                   ls.find_flow_for_loc(loc, flows)) for loc in roads)
	
    for n, data in G.nodes_iter(data=True):
        data['pos'] = n
        
    if flow == True:
        for m, n, data in G.in_edges_iter(data=True):
            data['flow'] = ls.find_flow_for_long_lat(tuple((m,n)), line_flows)
            
    if occupancy == True:
        pass
    
    if speed == True:
        pass
    
    return G

def lines_from_digraph(digraph):
    
    lines = []
    l_flows = []
    
    for m, n, data in digraph.in_edges_iter(data=True):
        lines.append((m,n))
        l_flows.append(float(data['flow']))
        
    return lines, l_flows

def draws_the_graph(digraph):
    
    # Draws the network
    nx.draw_networkx(digraph, pos=dict((n, n) for n in digraph.nodes_iter()))
    nx.draw_networkx_edge_labels(
        digraph,
        pos=dict((n, n) for n in digraph.nodes_iter()),
        edge_labels=dict(((u,v),d['flow']) for u, v, d in digraph.edges_iter(data=True))
    )
    axis('equal');

def edge_weight(u, v, s):
    """
    The "weight" or "length" of an edge is going to be the time taken to traverse it.
    """
    delta = np.array(u) - np.array(v)
    length = np.sqrt(np.sum(delta * delta))
    time = length / s
    return time

def astar_heuristic(n1, n2):
    """A function to evaluate the estimate of the distance from the a node
    to the target. The function takes two nodes arguments and must return a number.
    """
    average_speed = 70
    return edge_weight(n1, n2, 70)

def node_adjacencies(digraph):   
    
    adjacencies = []
    for m,n in digraph.adjacency_iter():
        if len(n)==1:
            adjacencies.append(1)
        else:
            adjacencies.append(0)
    
    from itertools import product
    b = 0
    cnt = digraph.order()
    node_adjacencies = []
    for n1,n2 in product(digraph.nodes_iter(),digraph.nodes_iter()):
        node_adjacencies.append(adjacencies[b // cnt])
        b += 1
        
    return node_adjacencies

def best_paths(digraph, node_adjacents):    
    
    # Compute a path for each possible pair of nodes
    from itertools import product
    # n_pairs = G.order()**2 - G.order()
    best_paths = { }
    na_cnt = 0
    cnt = digraph.order()
    for n1, n2 in product(digraph.nodes_iter(), digraph.nodes_iter()):
        na_cnt += 1
        if n1 is n2:
            continue
        if node_adjacents[na_cnt-1]==0:
            continue
        if node_adjacents[((na_cnt-1)%cnt)*cnt]==0:
            continue
        try:
            best_paths[(n1, n2)] = nx.astar_path(digraph, n1, n2, astar_heuristic)
        except:
            pass
            
    print('Computed {0} paths. Expected to compute {1}'.format(
        len(best_paths), digraph.order()**2 - digraph.order()
    ))
    
    return best_paths

def path_to_edges(path):
    """Convert a path specified as a list of nodes into a list of edges."""
    return list((u, v) for u, v in zip(path[:-1], path[1:]))

def create_routing_matrix(best_paths, digraph):
    
    routes = list(best_paths.keys())
    edges = digraph.edges()
    
    # Our routing matrix has #edge rows and #routes columns
    routing = np.zeros((len(edges), len(routes)))
    # For each route...
    for r_idx, r in enumerate(routes):
        # Which edges are in this path?
        edge_idxs = list(edges.index(e) for e in path_to_edges(best_paths[r]))
        routing[edge_idxs, r_idx] = 1
        
    return routing

def estimate_routes_least_norm(edge_occupancy, routing):
    return np.linalg.lstsq(routing, edge_occupancy)[0]

from sklearn import linear_model as lm
from sklearn.preprocessing import normalize

def estimate_routes_sparse(edge_occupancy, routing, sparsity):
    '''The lower the sparsity number, the sparser the resultant matrix'''
    #return lm.orthogonal_mp(routing,edge_occupancy,sparsity)
    return lm.orthogonal_mp(np.transpose(normalize(np.transpose(routing),"l2",1)),edge_occupancy,sparsity)

def create_thresholded_digraph(l_flows, threshold, best_paths, routing):  
    
    routes = list(best_paths.keys())
    flows = np.array(l_flows)
    
    # Creates a directed graph object to display notable flows
    flow_thresh = 1
    routeG = nx.DiGraph()
    ersln = estimate_routes_sparse(flows,routing,threshold);
    for r, f in zip(routes, ersln):
        if f < flow_thresh:
            continue
        n1, n2 = r
        routeG.add_edge(n1, n2, dict(label='{0:.02}'.format(f), flow=f))
        
    return routeG

