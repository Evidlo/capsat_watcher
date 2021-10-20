#!/usr/bin/env python
# Capsat beacon parser and uploader
# 2021-10-19 - Jatin Mathur, Logan Power, Evan Widloski

import argparse
import datetime
import json
import logging
from pathlib import Path
import requests
from struct import unpack
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

log = logging.getLogger('capsat_watcher')
logging.basicConfig(format='%(message)s', level=logging.INFO)

# we check that these RecordSources exist in django before uploading
# (RecordSource name, data type, data size)
BEACON_FORMAT = {
    ('sync', '<H', 2),
    ('host_id', '<B', 1),
    ('system_time', '<I', 4),
    ('custom_data0', '<B', 1),
    ('custom_data1', '<B', 1),
    ('custom_data2', '<B', 1),
    ('custom_data3', '<B', 1),
    ('quaternions0', '<f', 4),
    ('quaternions1', '<f', 4),
    ('quaternions2', '<f', 4),
    ('quaternions3', '<f', 4),
    ('rates0', '<f', 4),
    ('rates1', '<f', 4),
    ('rates2', '<f', 4),
    ('illumination_state', '<H', 2),
    ('algorithm', '<B', 1),
    ('battery_voltage0', '<f', 4),
    ('battery_voltage1', '<f', 4),
    ('battery_voltage2', '<f', 4),
    ('battery_voltage3', '<f', 4),
    ('battery_temperature0', '<f', 4),
    ('battery_temperature1', '<f', 4),
    ('battery_temperature2', '<f', 4),
    ('battery_temperature3', '<f', 4),
}

BEACON_FILE_PREFIX = 'beacon_'

# watchdog class
class Handler(FileSystemEventHandler):
    def __init__(self, *, target, token):
        self.target = target
        self.token = token

    def on_created(self, event):
        # Upload newly created beacons
        beacon_path = Path(event.src_path)
        if not beacon_path.name.startswith(BEACON_FILE_PREFIX):
            return
        log.info(f"Detected new beacon at {beacon_path}")
        upload_beacon(
            target=self.target,
            token=self.token,
            beacon_path=beacon_path
        )


def upload_beacon(*, target, token, beacon_path):
    """Upload beacon data to target server

    Creates one Record in django for each datapoint in the beacon data

    Arguments:
        target (str): host + port of target django server
        token (str): django token string
        beacon_path (str): beacon file path
    """
    beacon_path = Path(beacon_path)

    date, data = parse_beacon(beacon_path)

    log.info("Uploading beacon data to MOC")

    # loop through beacon data and upload each as a Record
    for rs, value in data.items():
        r = requests.post(
            target + '/api/objects/records/',
            headers={"Authorization": token},
            data={
                "created_at": date.isoformat(),
                "value": value,
                "source": rs
            },
        )
        if not r.ok:
            open('error.html', 'wb').write(r.content)
            log.error("Got an error from MOC. Saving to error.html")
            return

    log.info(f"Processed {beacon_path.name}")
    beacon_path.rename(beacon_path.parent.joinpath('processed_' + beacon_path.name))

def parse_beacon(filename):
    """
    Parse beacon file into date and data

    Arguments:
        filename (pathlib.Path): path to beacon file

    Returns:
        A length 2 tuple containing beacon date (datetime) and beacon data (dict)
    """
    date = datetime.datetime.strptime(filename.name, "beacon_%Y-%m-%d_%H:%M:%S")
    date = date.replace(tzinfo=datetime.timezone.utc)

    # check beacon buffer size before unpacking
    f = open(filename, 'rb')
    num_bytes = len(f.peek())
    if num_bytes != 74:
        log.error(f"Incorrect beacon size.  Got {num_bytes} bytes")

    # unpack beacon data into dict
    data = {}
    for rs, t, s in BEACON_FORMAT:
        data[rs] = unpack(t, f.read(s))

    return date, data

def check_database(*, target, token):
    """Verify that database has the RecordSources we need

    Arguments:
        target (str): host + port of target django server
        token (str): django token string
    """

    log.info("Checking Django has the RecordSources we need")

    # get list of existing RecordSources
    url = target + '/api/objects/record_sources/'
    record_sources = requests.get(
        url,
        headers={"Authorization": token},
    )
    record_sources.raise_for_status()
    j = json.loads(record_sources.content)
    django_record_sources = [rs['suffix'] for rs in j['results']]
    expected_record_sources = [rs[0] for rs in BEACON_FORMAT]

    # compare existing vs expected RecordSources
    if set(django_record_sources) != set(expected_record_sources):
        log.error("Django database is missing expected RecordSources")
        log.error(f"Expected: {expected_record_sources}")
        log.error(f"Got: {django_record_sources}")
        raise Exception

def main():
    parser = argparse.ArgumentParser("Beacon watcher")
    parser.add_argument('--token', type=str, help="django auth token")
    parser.add_argument('--path', type=str, help="directory containing existing/new beacons")
    parser.add_argument('--target', type=str, help="URL prefix to post data to")
    parser.add_argument('--debug', action='store_true', default=False, help="enable debugging")

    args = parser.parse_args()

    if args.debug:
        log.setLevel(logging.DEBUG)

    # token should have "Token " prefix
    args.token = "Token " + args.token

    # check target server to make sure Django RecordSources exist before uploading
    check_database(target=args.target, token=args.token)

    # upload existing beacons
    for beacon_path in Path(args.path).glob(BEACON_FILE_PREFIX + '*'):
        upload_beacon(
            target=args.target,
            token=args.token,
            beacon_path=beacon_path
        )

    # watch for newly created beacons in args.path
    handler = Handler(target=args.target, token=args.token)
    observer = Observer()
    path = Path(args.path)
    observer.schedule(event_handler=handler, path=args.path)
    observer.start()

    log.info(f"Watching directory {path.resolve()}")

    try:
        while observer.is_alive():
            observer.join(1)
    finally:
        observer.stop()
        observer.join()

if __name__ == '__main__':
    main()
