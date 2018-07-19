import copy
import csv
import itertools
import json
import argparse

import numpy as np

import local_io as io


class CorrectionZone:
    def __init__(self, horizontal_zones=1, vertical_zones=1):
        """
        :param horizontal_zones: the number of zones that should exist along the x axis
        :param vertical_zones: the number of zones that should exist along the y axis
         _ _ _
        |_|_|_|
        |_|_|_|
        A region with three horizontal zones and two vertical zones. A horizontal zone is formed
        by two vertical lines. A vertical zone is formed by two horizontal lines.
        """
        """ manually collected points. the ith point in each list corresponds to the ith sample. """
        source_samples = self.__load_data('aimsun_samples')
        target_samples = self.__load_data('google_samples')

        self.horizontal_zones = horizontal_zones
        self.vertical_zones = vertical_zones

        """ compute the min/max lon/lats to bounds for each zone. """
        min_lon = min(source_samples, key=lambda p: p[0])[0]
        max_lon = max(source_samples, key=lambda p: p[0])[0]
        self.lon_bounds = self.__find_bounds(min_lon, max_lon, horizontal_zones)

        min_lat = min(source_samples, key=lambda p: p[1])[1]
        max_lat = max(source_samples, key=lambda p: p[1])[1]
        self.lat_bounds = self.__find_bounds(min_lat, max_lat, vertical_zones)

        """ construct each zone, represented as a list of lists. """
        source_bucket = [[list() for _ in range(horizontal_zones)] for _ in range(vertical_zones)]
        target_bucket = copy.deepcopy(source_bucket)
        self.transformation_matrices = copy.deepcopy(source_bucket)

        print('partitioning points into {0} horizontal and {1} vertical zones, for a total of {2} zones.'
              .format(horizontal_zones, vertical_zones, horizontal_zones * vertical_zones))
        for bucket in source_bucket:
            print(bucket)

        """ add element for constant offset in linear regression"""
        source_samples = list(map(lambda point: point + [1], source_samples))

        """ iterate through sample data. build parallel buckets of sample and real data. """
        for data_point, real_point in zip(source_samples, target_samples):
            i, j = self.__bucket_index(data_point)
            source_bucket[i][j].append(data_point)
            target_bucket[i][j].append(real_point)

        print('# of control points per zone. warning: zones with fewer than 3 sample points will not be corrected.')
        for bucket in source_bucket:
            s = str([len(inner) for inner in bucket])
            print(s)

        """ construct each transformation matrix. """
        for i, j in itertools.product(range(vertical_zones), range(horizontal_zones)):
            source = source_bucket[i][j]
            target = target_bucket[i][j]
            if len(source) >= 3:
                """ lstsq(P, Q) -> x | Q = Px """
                t = np.linalg.lstsq(source, target, rcond=None)[0]
            else:
                t = np.linalg.lstsq([[1, 1, 1]], [[1, 1]], rcond=None)[0]
            self.transformation_matrices[i][j] = t

    def __bucket_index(self, point):
        """
        given a point, returns the indices of the bucket that it should be assigned to
        :param point: a list of the form, [lon, lat]
        :return: two integers
        """
        try:
            lon_index = next(i for i in range(self.horizontal_zones) if point[0] <= self.lon_bounds[i])
        except StopIteration:
            lon_index = len(self.lon_bounds) - 1

        try:
            lat_index = next(i for i in range(self.vertical_zones) if point[1] <= self.lat_bounds[i])
        except StopIteration:
            lat_index = len(self.lat_bounds) - 1

        return lat_index, lon_index

    def correct_point(self, p):
        p_as_list = [p['longitude'], p['latitude'], 1]
        i, j = self.__bucket_index(p_as_list)
        # print(p_as_list, self.transformation_matrices[i][j])
        transformed = np.dot(p_as_list, self.transformation_matrices[i][j])
        return {'longitude': transformed[0], 'latitude': transformed[1]}

    @staticmethod
    def __load_data(file):
        with open(file + '.csv', 'r') as f:
            return list(map(lambda p: [float(v) for v in p], csv.reader(f)))

    @staticmethod
    def __find_bounds(minimum, maximum, zone_count):
        """
        :param minimum: the smallest value in a data set
        :param maximum:  the largest value in a data set
        :param zone_count: the number of zones that should be defined
        :return: a list of zone_count values defining the upper bound of each bucket
        """
        bucket_size = (maximum - minimum) / zone_count
        return [minimum + (i * bucket_size) for i in range(1, zone_count + 1)]


parser = argparse.ArgumentParser()
parser.add_argument("-horizontal", type=int,
                    help="the number of horizontal zones")
parser.add_argument("-vertical", type=int,
                    help="the number of vertical zones")
args = parser.parse_args()

assert args.horizontal and args.vertical, "-h, -v are required. example usage: \'py correct_distortion.py -h 2 -v 1\'"

cz = CorrectionZone(args.horizontal, args.vertical)

unprocessed_json = io.get_JSON_strings()

for key in filter(lambda name: 'corrected' not in name, unprocessed_json.keys()):
    print('Correcting', key)
    tmdd_object_system = json.loads(unprocessed_json[key])

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
        link['link-begin-node-location'] = cz.correct_point(link['link-begin-node-location'])
        link['link-end-node-location'] = cz.correct_point(link['link-end-node-location'])
        link['link-geom-location'] = [cz.correct_point(p) for p in link['link-geom-location']]

    for node in node_inventory:
        node['node-location'] = cz.correct_point(node['node-location'])

    path = io.get_script_path('data')
    io.write_tmdd_json(tmdd_object_system, path, key + '_corrected_' + str(cz.horizontal_zones) + 'x' + str(cz.vertical_zones))
