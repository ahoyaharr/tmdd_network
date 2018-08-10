import json
import local_io as io
from shapely.geometry.point import Point 
from shapely.geometry.linestring import LineString

""" extracts the coordinates of each corrected .json file in the ~/tmdd_network/data/ directory. """

data_files = io.get_JSON_strings()

for key in filter(lambda name: 'corrected' in name, data_files.keys()):
    print('processing {0}.json'.format(key))
    tmdd_object_system = json.loads(data_files[key])
    link_inventory = tmdd_object_system['LinkInventory']['link-inventory-list']

    """ build and write the .csv for visualising the network. id is a fake id, enumerating the
    total number of links. """
    data = []
    for count, link in enumerate(link_inventory):
        link_points = link['link-geom-location']
        for source, target in zip(link_points[:-1], link_points[1:]):
            source_point = Point(source['longitude'], source['latitude'])
            target_point = Point(target['longitude'], target['latitude'])
            edge = LineString((source_point, target_point))
            data.append(
                {'source': source_point.wkb_hex,
                 'target': target_point.wkb_hex,
                 'edge': edge.wkb_hex,
                 'id': count})
    io.export(['source', 'target', 'edge', 'id'], data, key)
