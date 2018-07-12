import csv
import os
import sys
import json


def separator():
    UNIX_ENCODING = '/'
    WINDOWS_ENCODING = '\\'
    return WINDOWS_ENCODING


def get_script_path(p):
    return os.path.dirname(os.path.realpath(sys.argv[0])) + separator() + p


def get_JSON_files(path='data', absolute=False):
    # Returns a list of paths to uncorrected files in a directory.
    # path: the path to the directory
    # absolute: whether or not the filePath should be relative, i.e. ~/myFile.file vs. ~/.../myFile.file
    # system_type: 'windows' or 'unix'
    files = [file for file in os.listdir(get_script_path(path)) if '.json' in file]
    return [get_script_path(path) + separator() + file for file in files] if absolute else files


def read_file(s, dir='data'):
    file = open(os.path.dirname(os.path.realpath(sys.argv[0])) + separator() + dir + separator() + s)
    return file.read()


def get_JSON_strings():
    """
    Maps the file name without the extension to the associated JSON string.
    """
    return {file.rsplit(".", 1)[0]: read_file(file) for file in get_JSON_files()}


def export(header, data, filename):
    """
    Write a CSV as defined by the header, and the dictionaries holding data to the ~/exports/ directory.
    :param header: A sequence of strings of length k, where each item is a column name
    :param data: A sequence of tuples each of length k, where each item in a row in the relation.
    :return: True if successful, otherwise False
    """
    assert type(data) is list and len(data) > 0  # Data must be a list containing data.
    assert type(header) is list and len(header) > 0  # Header must be a list containing data.

    for row in data:
        # Each row must be a dictionary, and the keys of the dictionary must be aligned with the header.
        assert len(header) == len(row.keys()) and type(row) is dict

    filepath = get_script_path('data') + separator() + filename + '.csv'
    with open(filepath, 'w', newline='\n') as csvfile:
        f = csv.DictWriter(csvfile, fieldnames=header, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)

        f.writeheader()
        for row in data:
            f.writerow(row)

def write_tmdd_json(tmdd_object, path, filename):
    tmdd_json = json.dumps(tmdd_object, indent=2)

    tmdd_path = path + separator() + filename + '.json'
    with open (tmdd_path, 'w') as text_file:
        text_file.write(tmdd_json)