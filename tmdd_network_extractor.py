from PyANGBasic import *
from PyANGKernel import *
from PyANGGui import *
from PyANGAimsun import *
#from AAPI import *

import datetime
import pickle
import sys
import csv
import os
import json
import math

WINDOWS_ENCODING = '\\'
UNIX_ENCODING = '/'

SYSTEM_TYPE = 'windows'

MPH_CONSTANT = 0.62137119 # multiply km/hr to convert to mph

translator = GKCoordinateTranslator(model)    


def build_geolocation(translator, coordinate_pair):
    '''
    Converts an untranslated coordinate pair into a dictionary
    mapping 'lon'/'lat' -> coordinate value.
    '''
    coordinate = translator.toDegrees(coordinate_pair)
    return {'longitude': coordinate.x, 'latitude': coordinate.y}

def build_organization_information(organization_id):
    return {'organization-id': organization_id}

def build_update_time():
    return {'date': str(datetime.date.today()), 'time': str(datetime.datetime.now().time()), 'offset': -8}

def build_tmdd_map(model, organization_id, network_id, network_name):
    def build_node_inventory_element(junction_object):
        print 'starting node inventory'
        element = dict()
        element['network-id'] = network_id  # Required
        element['network-name'] = network_name  # Required
        element['node-id'] = str(junction_object.getId())  # Required 
        element['node-name'] = junction_object.getName()
        element['node-location'] = build_geolocation(translator, junction_object.getPosition())
        element['last-update-time'] = build_update_time()
        return element

    def build_node_status_element(junction_object):
        print 'starting node status'
        element = dict()
        element['network-id'] = network_id  # Required
        element['network-name'] = network_name  # Required
        element['node-id'] = str(junction_object.getId())  # Required 
        element['node-name'] = junction_object.getName()
        element['last-update-time'] = build_update_time()
        element['node-status'] = 'no determination'
        return element 

    def build_link_inventory_element(section_object):
        print 'starting link inventory'
        element = dict()
        element['network-id'] = network_id  # Required
        element['network-name'] = network_name  # Required
        element['link-id'] = str(section_object.getId())  # Required 
        element['link-name'] = section_object.getName()
        element['link-type'] = str(section_object.getRoadType())  # Required
        begin_node = section_object.getOrigin()
        if begin_node is not None:
            element['link-begin-node-id'] = str(begin_node.getId())  # Required
            element['link-begin-node-location'] = build_geolocation(translator, begin_node.getPosition())  # Required
        else:
            element['link-begin-node-id'] = 'None'
            element['link-begin-node-location'] = {'latitude': 0.0, 'longitude': 0.0}
        end_node = section_object.getDestination()
        if end_node is not None:
            element['link-end-node-id'] = str(end_node.getId())  # Required
            element['link-end-node-location'] = build_geolocation(translator, end_node.getPosition())  # Required
        else:
            element['link-end-node-id'] = 'None'
            element['link-end-node-location'] = {'latitude': 0.0, 'longitude': 0.0}
        element['link-speed-limit'] = section_object.getSpeed() * MPH_CONSTANT
        element['link-speed-limit-units'] = 'miles per hour'
        element['last-update-time'] = build_update_time()
        element['link-geom-location'] = [build_geolocation(translator, point) for point in section_object.calculatePolyline()]
        element['link-geom-location'].append(element['link-end-node-location'])
        element['link-geom-location'].insert(0, element['link-begin-node-location'])
        return element

    def build_link_status_element(section_object):
        print 'starting link status'
        element = dict()
        element['network-id'] = network_id  # Required
        element['network-name'] = network_name  # Required
        element['link-id'] = str(section_object.getId())  # Required 
        element['link-name'] = section_object.getName()
        element['link-status'] = 'no determination' 
        element['last-update-time'] = build_update_time()
        return element

    link_inventory = []
    link_status = []
    node_inventory = []
    node_status = []

    for types in model.getCatalog().getUsedSubTypesFromType(model.getType('GKSection')):
        for section_object in types.itervalues():
            link_inventory.append(build_link_inventory_element(section_object))
            link_status.append(build_link_status_element(section_object))

    for types in model.getCatalog().getUsedSubTypesFromType(model.getType('GKNode')):
        for junction_object in types.itervalues():
            node_inventory.append(build_node_inventory_element(junction_object))
            node_status.append(build_node_status_element(junction_object))

    return {'LinkInventory': {'organization-information': build_organization_information(organization_id),
                              'link-inventory-list': link_inventory},
            'LinkStatus': {'organization-information': build_organization_information(organization_id),
                              'link-inventory-list': link_status},
            'NodeInventory': {'organization-information': build_organization_information(organization_id),
                              'link-inventory-list': node_inventory},
            'NodeStatus': {'organization-information': build_organization_information(organization_id),
                              'link-inventory-list': node_status}}

def separator():
    return WINDOWS_ENCODING if SYSTEM_TYPE == 'windows' else UNIX_ENCODING

def build_json(model, path, organization_id, network_id, network_name):
    tmdd_map = build_tmdd_map(model, organization_id, network_id, network_name)

    tmdd_json = json.dumps(tmdd_map, indent=2)

    tmdd_path = path + separator() + 'tmdd.json'
    print 'Writing', tmdd_path
    with open (tmdd_path, 'w') as text_file:
        text_file.write(tmdd_json)

gui=GKGUISystem.getGUISystem().getActiveGui()
model = gui.getActiveModel()

path='C:\Users\Serena\connected_corridors\tmdd_network\tmdd_network\data'

build_json(model, path, 'connected_corridors', '409', 'tmdd_network')