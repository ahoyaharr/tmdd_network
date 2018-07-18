from PyANGBasic import *
from PyANGKernel import *
from PyANGGui import *
from PyANGAimsun import *

import datetime
import json

WINDOWS_ENCODING = '\\'
UNIX_ENCODING = '/'

SYSTEM_TYPE = 'windows'

MPH_CONSTANT = 0.62137119 # multiply km/hr to convert to mph

DUMMY_ID = 0

translator = GKCoordinateTranslator(model)    


def build_geolocation(translator, coordinate_pair):
    """
    Converts an untranslated coordinate pair into a dictionary
    mapping 'lon'/'lat' -> coordinate value.
    """
    coordinate = translator.toDegrees(coordinate_pair)
    return {'longitude': coordinate.x, 'latitude': coordinate.y}

def build_organization_information(organization_id):
    return {'organization-id': organization_id}

def build_update_time():
    return {'date': str(datetime.date.today()), 'time': str(datetime.datetime.now().time()), 'offset': '-8'}

def road_to_tmdd(road_type):
    """
    Converts Aimsun road types to TMDD valid field type.
    :param type: A string of the Aimsun road type.
    """
    aimsun_to_tmdd = {'street': 'arterial', 'freeway hov lane': 'dedicated-hov-link', 'off ramp': 'off-ramp',
                      'on ramp': 'on-ramp', 'light rail track': 'railroad link', 'freeway connector': 'freeway'}
    return aimsun_to_tmdd[road_type] if road_type in aimsun_to_tmdd else road_type

def build_tmdd_map(model, organization_id, network_id, network_name):
    def build_node_inventory_element(junction_object):
        element = dict()
        element['network-id'] = network_id  # Required
        element['network-name'] = network_name  # Required
        element['node-id'] = str(junction_object.getId())  # Required 
        element['node-name'] = junction_object.getName()
        element['node-location'] = build_geolocation(translator, junction_object.getPosition())
        element['last-update-time'] = build_update_time()
        # signalized = model.getType("GKNode").getColumn("GKNode:signalizedIntersection", GKType.eSearchOnlyThisType)
        # element['node-description'] = "Signalized" if signalized else "Not signalized"

        return element

    def build_node_status_element(junction_object):
        element = dict()
        element['network-id'] = network_id
        element['network-name'] = network_name
        element['node-id'] = str(junction_object.getId())
        element['node-name'] = junction_object.getName()
        element['last-update-time'] = build_update_time()
        element['node-status'] = 'no determination'
        return element 

    def build_link_inventory_element(section_object):
        global DUMMY_ID

        element = dict()
        element['network-id'] = network_id
        element['network-name'] = network_name
        element['link-id'] = str(section_object.getId())
        element['link-name'] = section_object.getName()
        element['link-type'] = road_to_tmdd(section_object.getRoadType().getName().lower())
        element['link-capacity'] = int(section_object.getCapacity())
        element['link-length'] = max((section_object.getLaneLength(i) for i in range(len(section_object.getLanes()))))

        """ Build the link geometry, sans the source and target nodes. """
        element['link-geom-location'] = [build_geolocation(translator, point) for point in section_object.calculatePolyline()]

        """ Find and update the source/target nodes, if they exist. If they do not exist, create a symbolic
        node with location equal to the beginning/end point in the link geometry. """
        begin_node = section_object.getOrigin()
        if begin_node is not None:
            element['link-begin-node-id'] = str(begin_node.getId())  # Required
            element['link-begin-node-location'] = build_geolocation(translator, begin_node.getPosition())  # Required
            city = model.getType("GKDPoint").getColumn("GKDPoint::CITY", GKType.eSearchOnlyThisType)
            element['link-jurisdiction'] = begin_node.getDataValue(city)[0] if (begin_node.getDataValue(city)[0]) is not None else "Data not provided"
        else:
            DUMMY_ID = DUMMY_ID + 1
            element['link-begin-node-id'] = 'dummy' + str(DUMMY_ID)
            element['link-begin-node-location'] = element['link-geom-location'][0]
        end_node = section_object.getDestination()
        if end_node is not None:
            element['link-end-node-id'] = str(end_node.getId())  # Required
            element['link-end-node-location'] = build_geolocation(translator, end_node.getPosition())  # Required
        else:
            DUMMY_ID = DUMMY_ID + 1
            element['link-end-node-id'] = 'dummy' + str(DUMMY_ID)
            element['link-end-node-location'] = element['link-geom-location'][-1]

        """ After the source/target nodes are updated, append them to the link geometry. """
        element['link-geom-location'].append(element['link-end-node-location'])
        element['link-geom-location'].insert(0, element['link-begin-node-location'])

        element['link-speed-limit'] = section_object.getSpeed() * MPH_CONSTANT
        element['link-speed-limit-units'] = 'miles per hour'
        element['last-update-time'] = build_update_time()

        return element

    def build_link_status_element(section_object):
        element = dict()
        element['network-id'] = network_id  # Required
        element['network-name'] = network_name  # Required
        element['link-id'] = str(section_object.getId())  # Required 
        element['link-name'] = section_object.getName()
        element['link-status'] = 'no determination' 
        element['last-update-time'] = build_update_time()
        element['link-lanes-count'] = section_object.getNbFullLanes()
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
                              'link-status-list': link_status},
            'NodeInventory': {'organization-information': build_organization_information(organization_id),
                              'node-inventory-list': node_inventory},
            'NodeStatus': {'organization-information': build_organization_information(organization_id),
                              'node-status-list': node_status}}

def separator():
    return WINDOWS_ENCODING if SYSTEM_TYPE == 'windows' else UNIX_ENCODING

def build_json(model, path, filename, organization_id, network_id, network_name):
    tmdd_map = build_tmdd_map(model, organization_id, network_id, network_name)

    tmdd_json = json.dumps(tmdd_map, indent=2)

    tmdd_path = path + separator() + filename + '.json'
    print 'Writing', tmdd_path
    with open (tmdd_path, 'w') as text_file:
        text_file.write(tmdd_json)

gui=GKGUISystem.getGUISystem().getActiveGui()
model = gui.getActiveModel()

path = 'C:\Users\serena\connected_corridors\\tmdd_network\data'
build_json(model, path, 'tmdd_v00', 'PATH Connected Corridors', '2018-06-14a', 'I-210 Pilot Aimsun TMDD Network v00')
