import json

import numpy as np

import local_io as io


def update_point(p, t):
    """
    :param p: a dictionary with 'latitude' and 'longitude' fields.
    :param t: a transformation matrix | [x1, y1, 1] * transformation_matrix = [x'1, y'1]
    :return: a dictionary with 'latitude' and 'longitude' fields containing transformed values.
    """
    transformed = np.dot([p['longitude', p['latitude'], 1]], t)
    return {'longitude': transformed[0], 'latitude': transformed[1]}


tmdd_object_system = json.loads(io.get_JSON_strings()['tmdd'])

""" manually collected points. the ith point in each list corresponds to the ith sample. """
aimsun_sample_points = [[]]
google_sample_points = [[]]

""" perform a least squares analysis on the two sets of sample points """
aimsun_sample_points = list(map(lambda point: point + [1], [[]]))
t = np.linalg.lstsq(aimsun_sample_points, google_sample_points)[0]  # The transformation matrix

""" 
transform and update each coordinate in the tmdd network.

fields to transform:
LinkInventory -> link-inventory-list -> link-begin-node-location -> p
                                     -> link-end-node-location -> p
                                     -> link-geom-location -> [p1, ..., pn]

NodeInventory -> node-inventory-list -> node-location -> p

"""
link_inventory = tmdd_object_system['LinkInventory']['link-inventory-list']
node_inventory = tmdd_object_system['NodeInventory']['node-inventory-list']

for link in link_inventory:
    link['link-begin-node-location'] = update_point(link['link-begin-node-location'], t)
    link['link-end-node-location'] = update_point(link['link-end-node-location'], t)
    link['link-geom-location'] = [update_point(p, t) for p in link['link-geom-location']]

for node in node_inventory:
    node['node-location'] = update_point(node['node-location'], t)


path = os.path.dirname(os.path.realpath(__file__)) + separator() + 'data'
build_json(tmdd_object_system, path, 'connected_corridors', 'tmdd_corrected')
