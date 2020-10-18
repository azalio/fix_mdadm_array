#!/usr/bin/env python3
"""Repair md array."""

# import json
import pickle
import sys
from contextlib import suppress

import blkinfo

from pymdstat import MdStat

db = '/root/disk.db'


def get_data_from_db(db: str) -> dict:
    """Get data from db.

    Args:
        db (str): Path to db

    Returns:
        dict: Dictionary with disk data

    """
    disk_data = {}
    # try:
    with suppress(FileNotFoundError):
        with open(db, 'rb') as file_handler:
            disk_data = pickle.load(file_handler)
    # except FileNotFoundError:
        # We assume new setup
        # pass
    return disk_data


def get_actual_data_from_system() -> dict:
    """Get data from lsblk.

    Returns:
        dict: Dictionary with disk data from system

    """
    myblkd = blkinfo.BlkDiskInfo()
    filters = {}
    return myblkd.get_disks(filters)


def clean_unnecessary_data(disk_data: dict) -> dict:
    """Clean unused data for simplicity.

    Args:
        disk_data (dict): Dictionary with data from lsblk

    Returns:
        dict: Dictionary with only useful disk data

    """
    for disk in disk_data:
        with suppress(KeyError):
            del(disk['statistics'])
    return disk_data


def write_data_to_db(disk_data: dict, db: str) -> None:
    """Write data to db.

    Args:
        disk_data (dict): Dictionary with data from lsblk
        db (str): Path to db

    """
    try:
        with open(db, 'wb') as file_handler:
            pickle.dump(disk_data, file_handler)
    except PermissionError:
        print('You need root priviledge for this programm')


def check_md_arrays() -> dict:
    """Check state of md arrays.

    Returns:
        dict: State of md arrays

    """
    md_status = {}

    mds = MdStat()
    md_arrays = mds.arrays()
    for md in md_arrays:
        if mds.type(md) == 'raid1':  # we only work with raid1
            # /sys/block/md126/md/array_state
            path_to_md_status = f'/sys/block/{md}/md/array_state'
            with open(path_to_md_status, 'r') as file_handler:
                status = file_handler.readline()
                status = status.strip()
            md_status[md] = status
    return md_status


if __name__ == '__main__':
    old_disk_data = get_data_from_db(db)
    if not old_disk_data:
        # Get status of md array and if 'clean' write data to db.
        state = check_md_arrays()
        if all(status == 'clean' for status in state.values()):
            disk_data = get_actual_data_from_system()
            disk_data = clean_unnecessary_data(disk_data)
            print('We assume that it new setup, so we write data to db')
            write_data_to_db(disk_data, db)

    disk_data = get_actual_data_from_system()
    disk_data = clean_unnecessary_data(disk_data)
    if disk_data == old_disk_data:
        # Nothing happened, we can leave job
        sys.exit(0)


# https://github.com/nicolargo/pymdstat
# https://github.com/fbrehm/nagios-plugin/blob/master/bin/check_swraid

# from peewee import *

# db = SqliteDatabase('disk.db')

# class BaseModel(Model):
#     class Meta:
#         database = db


# class Disk(BaseModel):
#     name = CharField(unique=True)
#     fstype = CharField()
#     size = CharField()
#     maj_min = CharField()
#     model = CharField()
#     vendor = CharField()
#     serial = CharField()
#     rota = CharField()
#     disk_type = CharField()
#     children = CharField()
#     parents = CharField()


# class MDArray(BaseModel):
#     pass

# class Disk(object):
#     def __init__(self):
#         pass


# myblkd = blkinfo.BlkDiskInfo()

# filters = {}

# filters = {
#     'type': 'disk',
#     'maj:min': '254:0',
#     # 'statistics': {
#     #     'major': '254',
#     # }
# }

# all_my_disks = myblkd.get_disks(filters)

# for disk in all_my_disks:
#     for k, v in disk.items():
#         print(f"k: {k}, v: {v}")

# json_output = json.dumps(all_my_disks)
# print(json_output)


# In [23]: for disk in all_my_disks:
#     ...:     if disk['type'] in ['disk', 'raid1']:
#     ...:         print(disk)
#     ...:         print(disk['name'])
#     ...:         print(disk['kname'])
#     ...:         print(disk['maj:min'])
#     ...:         print(disk['serial'])
#     ...:         print(disk['hctl'])
#     ...:         print(disk['tran'])
#     ...:         print(disk['rota'])
#     ...:         print(disk['children'])
#     ...:         print(disk['parents'])
#     ...:         print(disk['type'])
