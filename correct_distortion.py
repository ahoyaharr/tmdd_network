import json
import os
import itertools
import copy
import numpy as np
import local_io as io


class CorrectionZone:
    def __init__(self, source_samples, target_samples, horizontal_zones, vertical_zones):
        self.horizontal_zones = horizontal_zones
        self.vertical_zones = vertical_zones

        """ compute the min/max lon/lats to bounds for each zone. """
        min_lon = min(aimsun_sample_points, key=lambda p: p[0])[0]
        max_lon = max(aimsun_sample_points, key=lambda p: p[0])[0]
        self.lon_bounds = self.__find_bounds(min_lon, max_lon, horizontal_zones)

        min_lat = min(aimsun_sample_points, key=lambda p: p[1])[1]
        max_lat = max(aimsun_sample_points, key=lambda p: p[1])[1]
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
        print(list(itertools.product(range(vertical_zones), range(horizontal_zones))))
        for i, j in itertools.product(range(vertical_zones), range(horizontal_zones)):
            source = source_bucket[i][j]
            target = target_bucket[i][j]
            if len(source) >= 3:
                """ lstsq(P, Q) -> x | Q = Px """
                t = np.linalg.lstsq(source, target, rcond=None)[0]
            else:
                t = np.linalg.lstsq([[1, 1, 1]], [[1, 1]], rcond=None)[0]
            self.transformation_matrices[i][j] = t

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


# def update_point(p, t):
#     """
#     :param p: a dictionary with 'latitude' and 'longitude' fields.
#     :param t: a transformation matrix | [x1, y1, 1] * transformation_matrix = [x'1, y'1]
#     :return: a dictionary with 'latitude' and 'longitude' fields containing transformed values.
#     """
#     transformed = np.dot([p['longitude'], p['latitude'], 1], t)
#     return {'longitude': transformed[0], 'latitude': transformed[1]}
#
#
# def construct_sample_zones(points, number_horizontal_zones, number_vertical_zones):
#     """
#     :param points: a list of points in the form, [ [lon1, lat1], ...]
#     :param number_horizontal_zones: the number of zones that should exist along the x axis
#     :param number_vertical_zones: the number of zones that should exist along the y axis
#      _ _ _
#     |_|_|_|
#     |_|_|_|
#     A region with three horizontal zones and two vertical zones. A horizontal zone is formed
#     by two vertical lines. A vertical zone is formed by two horizontal lines.
#     """
#
#     def find_bounds(minimum, maximum, zone_count):
#         """
#         :param minimium: the smallest value in a data set
#         :param maximum:  the largest value in a data set
#         :param zone_count: the number of zones that should be defined
#         :return: a list of zone_count values defining the upper bound of each bucket
#         """
#         bucket_size = (maximum - minimum) / zone_count
#         return [minimum + (i * bucket_size) for i in range(1, zone_count + 1)]
#
#     def assign_bucket(buckets, point, lon_bounds, lat_bounds):
#         lon_index = next(i for i in range(number_horizontal_zones) if point[0] <= lon_bounds[i])
#         lat_index = next(i for i in range(number_vertical_zones) if point[1] <= lat_bounds[i])
#         buckets[lat_index][lon_index].append(point)
#
#     """ compute the min/max lon/lats to build correction zones. """
#     min_lon = min(aimsun_sample_points, key=lambda p: p[0])[0]
#     max_lon = max(aimsun_sample_points, key=lambda p: p[0])[0]
#     lon_bounds = find_bounds(min_lon, max_lon, number_horizontal_zones)
#
#     min_lat = min(aimsun_sample_points, key=lambda p: p[1])[1]
#     max_lat = max(aimsun_sample_points, key=lambda p: p[1])[1]
#     lat_bounds = find_bounds(min_lat, max_lat, number_vertical_zones)
#
#     buckets = [[list() for _ in range(number_horizontal_zones)] for _ in range(number_vertical_zones)]
#
#     for point in aimsun_sample_points:
#         assign_bucket(buckets, point, lon_bounds, lat_bounds)
#
#     return buckets


tmdd_object_system = json.loads(io.get_JSON_strings()['tmdd'])

""" manually collected points. the ith point in each list corresponds to the ith sample. """
aimsun_sample_points = [[-118.15591164484654, 34.1691006483424], [-118.15479455676724, 34.15567989605619],
                        [-118.15035177546658, 34.13569625764484], [-118.13251558237887, 34.161608372081126],
                        [-118.13241860230393, 34.152330499903556], [-118.13224327008102, 34.13583809919227],
                        [-118.09861765290997, 34.15444565088543], [-118.09867816164268, 34.14981793597448],
                        [-118.0910927205383, 34.12691549670491], [-118.08227575899828, 34.14825302799406],
                        [-118.07936417040581, 34.12149471071945], [-118.03166003906414, 34.14837830791005],
                        [-118.03158200756117, 34.14224047397803], [-118.03089244624877, 34.10723893029451],
                        [-118.00543432539888, 34.14586297240174], [-118.00518700635602, 34.134205936832345],
                        [-118.00323132080187, 34.11355897091589], [-117.96674635237359, 34.139677399387814],
                        [-117.95872487355346, 34.1342456387483], [-117.95179776459779, 34.13974509306353],
                        [-117.95180365752296, 34.136132469400096], [-117.93369522335487, 34.1335999029958],
                        [-117.93364714416435, 34.130582845136665], [-117.90533937809597, 34.12037072015765],
                        [-117.88398328797314, 34.12094376340619], [-118.1667931434251, 34.17948646057981],
                        [-118.18216461429898, 34.141920470663685], [-118.0913333687722, 34.11979002281881],
                        [-117.9835347840805, 34.10391387533825], [-117.98647658421594, 34.15155859157834]]
google_sample_points = [[-118.155894, 34.16906], [-118.154788, 34.155697], [-118.150382, 34.135779],
                        [-118.132468, 34.161577], [-118.132386, 34.152331], [-118.132257, 34.135856],
                        [-118.098544, 34.154416], [-118.098603, 34.149804], [-118.09107, 34.126962],
                        [-118.082183, 34.148244], [-118.079297, 34.121554], [-118.031602, 34.148348],
                        [-118.031496, 34.142247], [-118.030817, 34.107332], [-118.005301, 34.145854],
                        [-118.005092, 34.134233], [-118.003081, 34.11363], [-117.966616, 34.139688],
                        [-117.958892, 34.134376], [-117.951656, 34.139756], [-117.951664, 34.136141],
                        [-117.933538, 34.133666], [-117.933484, 34.130734], [-117.905203, 34.12046],
                        [-117.883801, 34.121045], [-118.166777, 34.179447], [-118.182363, 34.142031],
                        [-118.091267, 34.119864], [-117.983366, 34.104165], [-117.986337, 34.151538]]

cz = CorrectionZone(aimsun_sample_points, google_sample_points, 3, 2)

# """ perform a least squares analysis on the two sets of sample points """
# aimsun_sample_points = list(map(lambda point: point + [1], aimsun_sample_points))
# t = np.linalg.lstsq(aimsun_sample_points, google_sample_points, rcond=None)[0]  # The transformation matrix

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

# path = os.path.dirname(os.path.realpath(__file__)) + io.separator() + 'data'
path = io.get_script_path('data')
io.write_tmdd_json(tmdd_object_system, path, 'tmdd_corrected')
