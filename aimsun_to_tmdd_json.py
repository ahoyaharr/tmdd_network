from PyANGBasic import *
from PyANGKernel import *
from PyANGGui import *
from PyANGAimsun import *
from functools import reduce

import datetime
import json
import os

WINDOWS_ENCODING = '\\'
UNIX_ENCODING = '/'

SYSTEM_TYPE = 'windows'

MPH_CONSTANT = 0.62137119 # multiply km/hr to convert to mph

DUMMY_ID = 0
DIGIT_PRECISION = 7

translator = GKCoordinateTranslator(model)    


def build_geolocation(translator, coordinate_pair):
    """
    Converts an untranslated coordinate pair into a dictionary
    mapping 'lon'/'lat' -> coordinate value.
    """
    coordinate = translator.toDegrees(coordinate_pair)
    return {'longitude': coordinate.x, 'latitude': coordinate.y}

def build_organization_information(organization_id):
    return {'organization-id': organization_id, 'last-update-time': build_update_time()}

def build_update_time():
    return {'date': datetime.date.today().strftime("%Y%m%d"), \
            'time': datetime.datetime.now().strftime("%H%M%S%f")[:10]}

def road_to_tmdd(road_type):
    """
    Converts Aimsun road types to TMDD valid field type.
    :param type: A string of the Aimsun road type.
    """
    aimsun_to_tmdd = {'street': 'arterial', 'freeway hov lane': 'dedicated-hov-link', 'off ramp': 'off-ramp',
                      'on ramp': 'on-ramp', 'light rail track': 'railroad link', 'freeway connector': 'freeway'}
    return aimsun_to_tmdd[road_type] if road_type in aimsun_to_tmdd else road_type

def get_section_length(section_object):
    return max((section_object.getLaneLength(i) for i in range(len(section_object.getLanes()))))

def get_turnbay_length(section_object, flag):
    """
    Not used.
    :param flag: Indicates whether we want the left or right turning bay.
    """
    lanes = section_object.getLanes()
    num_lanes = len(lanes)
    turn_bay = 0 if (flag == 'left') else (num_lanes - 1)

    if not lanes[turn_bay].isFullLane():
        return int(round(lanes[turn_bay].getLength())) # units: meters
    else:
        return 0

def build_link_restrictions(section_object):
    return {'link-speed-limit': int(round((section_object.getSpeed() * MPH_CONSTANT))), \
            'link-speed-limit-units': 'miles-per-hour'}

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
      
    def build_dummy_node_element(link_element, begin):
        """
        link_element: dictionary containing information about a link inventory element
        begin: boolean value; TRUE if dummy is an origin node, else FALSE
        """
        position = 'begin' if begin else 'end'
        node_inventory.append({
              'network-id': link_element['network-id'],
              'network-name': link_element['network-name'],
              'node-id': link_element['link-{0}-node-id'.format(position)],
              'node-name': 'dummy_{0}_{1}'.format(position, link_element['link-name']),
              'node-location': link_element['link-{0}-node-location'.format(position)],
              'last-update-time': build_update_time()
            })
        node_status.append({
              'network-id': link_element['network-id'],
              'network-name': link_element['network-name'],
              'node-id': link_element['link-{0}-node-id'.format(position)],
              'node-name': 'dummy_{0}_{1}'.format(position, link_element['link-name']),
              'last-update-time': build_update_time(),
              'node-status': 'no determination'
            })
      

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
        element['link-length'] = int(round(get_section_length(section_object))) # units: meters
        element['link-restrictions'] = build_link_restrictions(section_object)

        """ Build the link geometry, sans the source and target nodes. """
        element['link-geom-location'] = [build_geolocation(translator, point) for point in section_object.calculatePolyline()]

        """ Find and update the source/target nodes, if they exist. If they do not exist, create a symbolic
        node with location equal to the beginning/end point in the link geometry. """
        begin_node = section_object.getOrigin()
        if begin_node is not None:
            element['link-begin-node-id'] = str(begin_node.getId())  # Required
            element['link-begin-node-location'] = build_geolocation(translator, begin_node.getPosition())  # Required
            # city = model.getType("GKDPoint").getColumn("GKDPoint::CITY", GKType.eSearchOnlyThisType)
            # element['link-jurisdiction'] = begin_node.getDataValue(city)[0] if (begin_node.getDataValue(city)[0]) is not None else "Data not provided"
        else:
            DUMMY_ID = DUMMY_ID + 1
            element['link-begin-node-id'] = 'dummy' + str(DUMMY_ID)
            element['link-begin-node-location'] = element['link-geom-location'][0]
            build_dummy_node_element(element, begin=True)
            
        end_node = section_object.getDestination()
        if end_node is not None:
            element['link-end-node-id'] = str(end_node.getId())  # Required
            element['link-end-node-location'] = build_geolocation(translator, end_node.getPosition())  # Required
        else:
            DUMMY_ID = DUMMY_ID + 1
            element['link-end-node-id'] = 'dummy' + str(DUMMY_ID)
            element['link-end-node-location'] = element['link-geom-location'][-1]
            build_dummy_node_element(element, begin=False)

        """ After the source/target nodes are updated, append them to the link geometry. """
        element['link-geom-location'].append(element['link-end-node-location'])
        element['link-geom-location'].insert(0, element['link-begin-node-location'])

        element['last-update-time'] = build_update_time()

        return element

    def build_link_status_element(section_object):
        element = dict()
        element['network-id'] = network_id  
        element['link-id'] = str(section_object.getId())  
        element['link-name'] = section_object.getName()
        element['link-status'] = 'no determination' 
        element['last-update-time'] = build_update_time()
        element['lanes-number-open'] = section_object.getNbFullLanes()
        return element

    def build_detour_route_inventory_element(subpath_object):
        element = dict()
        element['network-id'] = network_id
        element['network_name'] = network_name
        element['route-id'] = subpath_object.getId()
        element['route-link-id-list'] = [str(so.getId()) for so in subpath_object.getRoute()]
        element['route-type'] = 'detour'  # All SubPaths in models are for rerouting traffic
        element['route-name'] = subpath_object.getName()
        element['route-length'] = int(round(subpath_object.length3D())) # units: meters
        element['last-update-time'] = build_update_time()
        return element

    link_inventory = []
    link_status = []
    node_inventory = []
    node_status = []
    route_inventory = []

    for types in model.getCatalog().getUsedSubTypesFromType(model.getType('GKSection')):
        for section_object in types.itervalues():
            link_inventory.append(build_link_inventory_element(section_object))
            link_status.append(build_link_status_element(section_object))

    for types in model.getCatalog().getUsedSubTypesFromType(model.getType('GKNode')):
        for junction_object in types.itervalues():
            node_inventory.append(build_node_inventory_element(junction_object))
            node_status.append(build_node_status_element(junction_object))

    for types in model.getCatalog().getUsedSubTypesFromType(model.getType('GKSubPath')):
        for subpath_object in types.itervalues():
            if reduce(lambda prev, name: prev or name in subpath_object.getName(), ['EB_', 'WB_'], False):
                route_inventory.append(build_detour_route_inventory_element(subpath_object))

    """ A valid link must not be circular. Find all circular links by looking through link_inventory. """
    circular_links = reduce(
        lambda redundant, link: redundant + [link['link-id']] if link['link-begin-node-id'] == link['link-end-node-id'] else redundant,
        link_inventory,
        list())

    circular_link_predicate = lambda link: link['link-id'] not in circular_links


    """ A railway is not a valid link. Filter out all railroad links. """
    rail_links = reduce(
        lambda railway, link: railway + [link['link-id']] if link['link-type'] == 'railroad link' else railway,
        link_inventory,
        list())

    railroad_predicate = lambda link: link['link-id'] not in rail_links


    """ Filter invalid links. """
    link_inventory = list(filter(lambda link: circular_link_predicate(link) and railroad_predicate(link), link_inventory))
    link_status = list(filter(lambda link: circular_link_predicate(link) and railroad_predicate(link), link_status))


    return {'LinkInventory': {'organization-information': build_organization_information(organization_id),
                              'link-inventory-list': link_inventory},
            'LinkStatus': {'organization-information': build_organization_information(organization_id),
                              'link-status-list': link_status},
            'NodeInventory': {'organization-information': build_organization_information(organization_id),
                              'node-inventory-list': node_inventory},
            'NodeStatus': {'organization-information': build_organization_information(organization_id),
                              'node-status-list': node_status},
            'RouteInventory': {'organization-information': build_organization_information(organization_id), 
                              'route-inventory-list': route_inventory}}

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

path = os.getenv('APPDATA') + separator() + 'Aimsun' + separator() + 'Aimsun Next' + separator() + '8.2.0' + separator() + 'shared'
build_json(model, path, 'tmdd_v04', 'PATH Connected Corridors', '2018-10-4e', 'I-210 Pilot Aimsun TMDD Network v04')
