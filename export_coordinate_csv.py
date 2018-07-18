import json
import local_io as io

""" extracts the coordinates of each corrected .json file in the ~/tmdd_network/data/ directory. """

data_files = io.get_JSON_strings()

for key in filter(lambda name: 'corrected' in name, data_files.keys()):
    print('processing {0}.json'.format(key))
    tmdd_object_system = json.loads(data_files[key])
    link_inventory = tmdd_object_system['LinkInventory']['link-inventory-list']

    """ build and write the .csv for visualising the network """
    data = []
    for count, link in enumerate(link_inventory):
        for point in link['link-geom-location']:
            data.append({'lon': point['longitude'], 'lat': point['latitude'], 'id': count})
    io.export(['lat', 'lon', 'id'], data, key)
