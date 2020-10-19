#!/usr/bin/env python3
"""Repair md array."""

# import json
import pickle
import sys
from contextlib import suppress

import blkinfo

from pymdstat import MdStat

db = '/root/disk.db'

# https://github.com/canonical/curtin/blob/master/curtin/block/mdadm.py
"""
    clear
        No devices, no size, no level
        Writing is equivalent to STOP_ARRAY ioctl
    inactive
        May have some settings, but array is not active
           all IO results in error
        When written, doesn't tear down array, but just stops it
    suspended (not supported yet)
        All IO requests will block. The array can be reconfigured.
        Writing this, if accepted, will block until array is quiessent
    readonly
         no resync can happen.  no superblocks get written.
         write requests fail
    read-auto
        like readonly, but behaves like 'clean' on a write request.
    clean - no pending writes, but otherwise active.
        When written to inactive array, starts without resync
        If a write request arrives then
          if metadata is known, mark 'dirty' and switch to 'active'.
          if not known, block and switch to write-pending
        If written to an active array that has pending writes, then fails.
    active
        fully active: IO and resync can be happening.
        When written to inactive array, starts with resync
    write-pending
        clean, but writes are blocked waiting for 'active' to be written.
    active-idle
      like active, but no writes have been seen for a while (safe_mode_delay).
"""

ERROR_RAID_STATES = [
    'clear',
    'inactive',
    'suspended',
]

READONLY_RAID_STATES = [
    'readonly',
]

READWRITE_RAID_STATES = [
    'read-auto',
    'clean',
    'active',
    'active-idle',
    'write-pending',
]

VALID_RAID_ARRAY_STATES = (
    ERROR_RAID_STATES +
    READONLY_RAID_STATES +
    READWRITE_RAID_STATES
)


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


def get_failed_disks():
    ...


def get_jira_status():
    ...


def create_jira_ticket():
    ...


if __name__ == '__main__':
    old_disk_data = get_data_from_db(db)
    if not old_disk_data:  # If we don't have db.
        # Get status of md array and if 'clean' write data to db.
        state = check_md_arrays()
        if all(status in READWRITE_RAID_STATES for status in state.values()):
            disk_data = get_actual_data_from_system()
            disk_data = clean_unnecessary_data(disk_data)
            print('We assume that it new setup, so we write data to db')
            write_data_to_db(disk_data, db)

    disk_data = get_actual_data_from_system()
    disk_data = clean_unnecessary_data(disk_data)
    if disk_data == old_disk_data:
        # Nothing happened, we can leave job
        sys.exit(0)
    else:
        state = check_md_arrays()
        if all(status in READWRITE_RAID_STATES for status in state.values()):
            disk_data = get_actual_data_from_system()
            disk_data = clean_unnecessary_data(disk_data)
            print('We assume that it new setup, so we write data to db')
            write_data_to_db(disk_data, db)
        else:  # we have a trouble
            bad_disks = get_failed_disks()
            jira_status = get_jira_status()
            if not jira_status:
                create_jira_ticket()


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
