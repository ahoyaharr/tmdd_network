import json

import local_io as io

tmdd_object_system = json.loads(io.get_JSON_strings()['tmdd'])

link_inventory = tmdd_object_system['LinkInventory']['link-inventory-list']

""" build and write the .csv for visualising the network """
data = []
for count, link in enumerate(link_inventory):
    for point in link['link-geom-location']:
        data.append({'lon': point['longitude'], 'lat': point['latitude'], 'id': count})
io.export(['lat', 'lon', 'id'], data, 'tmdd')