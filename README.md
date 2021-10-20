# Capsat Beacon Uploader

Script to watch directory for new/existing Capsat beacons and upload them to a Django server.

Once beacons are processed, their filename will be added to a `.processed_beacons` file to prevent reupload.

## Quickstart

    $ pip install .
    $ capsat_watcher --target http://localhost:8000 --token XXXXXXXX --path path/to/beacons/
    
Obtain a token from Django like so:

    $ python manage.py drf_create_token moc
    Generated token XXXXXXXXXXXXXXXX for user moc
    
Or when using development server:


    $ python manage.py drf_create_token moc --settings moc.settings-dev
    Generated token XXXXXXXXXXXXXXXX for user moc

## Usage

usage: Beacon watcher [-h] [--token TOKEN] [--path PATH] [--target TARGET]

optional arguments:
  -h, --help       show this help message and exit
  --token TOKEN    django auth token
  --path PATH      directory containing existing/new beacons
  --target TARGET  URL prefix to send beacon data to
