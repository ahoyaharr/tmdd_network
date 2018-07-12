import json
import os
import numpy as np
import local_io as io


def update_point(p, t):
    """
    :param p: a dictionary with 'latitude' and 'longitude' fields.
    :param t: a transformation matrix | [x1, y1, 1] * transformation_matrix = [x'1, y'1]
    :return: a dictionary with 'latitude' and 'longitude' fields containing transformed values.
    """
    transformed = np.dot([p['longitude'], p['latitude'], 1], t)
    return {'longitude': transformed[0], 'latitude': transformed[1]}


tmdd_object_system = json.loads(io.get_JSON_strings()['tmdd'])

""" manually collected points. the ith point in each list corresponds to the ith sample. """
#aimsun_sample_points = [[-118.15728221723282, 34.17329775044658], [-118.06804078909138, 34.156854561382815], [-118.15453291100744, 34.127417535551025], [-117.98301162485568, 34.11421964581544]]
#google_sample_points = [[-118.157286, 34.173263], [-118.067961, 34.156799], [-118.154623, 34.127517], [-117.982822, 34.114232]]

aimsun_sample_points = [[-118.15591164484654, 34.1691006483424], [-118.15479455676724, 34.15567989605619], [-118.15035177546658, 34.13569625764484], [-118.13251558237887, 34.161608372081126], [-118.13241860230393, 34.152330499903556], [-118.13224327008102, 34.13583809919227], [-118.09861765290997, 34.15444565088543], [-118.09867816164268, 34.14981793597448], [-118.0910927205383, 34.12691549670491], [-118.08227575899828, 34.14825302799406], [-118.07936417040581, 34.12149471071945], [-118.03166003906414, 34.14837830791005], [-118.03158200756117, 34.14224047397803], [-118.03089244624877, 34.10723893029451], [-118.00543432539888, 34.14586297240174], [-118.00518700635602, 34.134205936832345], [-118.00323132080187, 34.11355897091589], [-117.96674635237359, 34.139677399387814], [-117.95872487355346, 34.1342456387483], [-117.95179776459779, 34.13974509306353], [-117.95180365752296, 34.136132469400096], [-117.93369522335487, 34.1335999029958], [-117.93364714416435, 34.130582845136665], [-117.90533937809597, 34.12037072015765], [-117.88398328797314, 34.12094376340619], [-118.1667931434251, 34.17948646057981], [-118.18216461429898, 34.141920470663685], [-118.0913333687722, 34.11979002281881], [-117.9835347840805, 34.10391387533825], [-117.98647658421594, 34.15155859157834]]
google_sample_points = [[-118.155894, 34.16906], [-118.154788, 34.155697], [-118.150382, 34.135779], [-118.132468, 34.161577], [-118.132386, 34.152331], [-118.132257, 34.135856], [-118.098544, 34.154416], [-118.098603, 34.149804], [-118.09107, 34.126962], [-118.082183, 34.148244], [-118.079297, 34.121554], [-118.031602, 34.148348], [-118.031496, 34.142247], [-118.030817, 34.107332], [-118.005301, 34.145854], [-118.005092, 34.134233], [-118.003081, 34.11363], [-117.966616, 34.139688], [-117.958892, 34.134376], [-117.951656, 34.139756], [-117.951664, 34.136141], [-117.933538, 34.133666], [-117.933484, 34.130734], [-117.905203, 34.12046], [-117.883801, 34.121045], [-118.166777, 34.179447], [-118.182363, 34.142031], [-118.091267, 34.119864], [-117.983366, 34.104165], [-117.986337, 34.151538]]


""" perform a least squares analysis on the two sets of sample points """
aimsun_sample_points = list(map(lambda point: point + [1], aimsun_sample_points))
t = np.linalg.lstsq(aimsun_sample_points, google_sample_points, rcond=None)[0]  # The transformation matrix

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


#path = os.path.dirname(os.path.realpath(__file__)) + io.separator() + 'data'
path = io.get_script_path('data')
io.write_tmdd_json(tmdd_object_system, path, 'tmdd_corrected')
