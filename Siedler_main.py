# imports
import csv
import os
from datetime import datetime, timedelta
from pathlib import Path
from time import sleep

import reverse_geocoder
from exif import Image
from orbit import ISS
from picamera import PiCamera
from skyfield.api import load

# variables:
cam = PiCamera()  # defining the camera
cam.resolution = (4056, 3040)  # defining the resolution
base_folder = Path(__file__).parent.resolve()  # Pathing variable to define the path in which the pictures are saved in
start_time = datetime.now()  # Create a `datetime` variable to store the start time
now_time = datetime.now()  # Create a `datetime` variable to store the current time
num = 0  # defines the loop count to zero
count = 0  # counter for data that is saved
exif_file = f'{base_folder}/coordinates.csv'

ephemeris = load('de421.bsp')
timescale = load.timescale()

end_time = datetime.now() + timedelta(minutes=179)  # Create a `datetime` variable to store the end time
max_filesize_in_gb = 2.9 # Define the maximum filesize in GB
print(end_time)

def convert(angle):
    """
    Convert a `skyfield` Angle to an EXIF-appropriate
    representation (rationals)
    e.g. 98° 34' 58.7 to "98/1,34/1,587/10"

    Return a tuple containing a boolean and the converted angle,
    with the boolean indicating if the angle is negative.
    """
    sign, degrees, minutes, seconds = angle.signed_dms()
    exif_angle = f'{degrees:.0f}/1,{minutes:.0f}/1,{seconds * 10:.0f}/10'
    return sign < 0, exif_angle


def capture(camera, image):
    # Use `camera` to capture an `image` file with lat/long EXIF data.
    point = ISS.coordinates()

    camera.capture(image)

    # Convert the latitude and longitude to EXIF-appropriate representations
    south, exif_latitude = convert(point.latitude)
    west, exif_longitude = convert(point.longitude)

    # Set the EXIF tags specifying the current location
    cam.exif_tags['GPS.GPSLatitude'] = exif_latitude
    cam.exif_tags['GPS.GPSLatitudeRef'] = "S" if south else "N"  # north-south latitude
    cam.exif_tags['GPS.GPSLongitude'] = exif_longitude
    cam.exif_tags['GPS.GPSLongitudeRef'] = "W" if west else "E"  # east-west longitude 
    return point


def get_remaining_space(path):
    size = 0  # Bytes
    for path, dirs, files in os.walk(path):
        for f in files:
            fp = os.path.join(path, f)
            size += os.stat(fp).st_size
    size = size / (1000 * 1000 * 1000)  # Filesize in GB
    return size


with open(exif_file, 'w') as file:  # defining the csv coordinate data file
    writer = csv.writer(file)
    header = (
        'Datetime',
        'North-South',
        'East-West',
        'Nearest city longitude',
        'Nearest city latitude',
        'Nearest city name',
        'Nearest city admin1',
        'Nearest city admin2',
        'Nearest city cc',
        )
    writer.writerow(header)
    
    enough_time = enough_space = True

    while enough_time and enough_space:
        enough_space = get_remaining_space(base_folder) < max_filesize_in_gb  # check if there is enough space in the folder
        enough_time = datetime.now() < end_time  # check if the time is still running

        t = timescale.now()
        if ISS.at(t).is_sunlit(ephemeris):
            num = num + 1  # counting the loop number to name the pictures
            capture_point = capture(cam, f'{base_folder}/gps{num:0>5n}.jpg')
            image_file = f'{base_folder}/gps{num:0>5n}.jpg'  # saving the pictures every loop named after the loop number
            capture(cam, image_file)

            coordinates = ISS.coordinates()
            coordinate_pair = (coordinates.latitude.degrees, coordinates.longitude.degrees)
            location = reverse_geocoder.search(coordinate_pair)
            lat, lon, name, admin1, admin2, cc = location[0].values()
            print(name)

            row = (
                datetime.now(),
                capture_point.latitude.degrees,
                capture_point.longitude.degrees,
                lat,
                lon,
                name,
                admin1,
                admin2,
                cc,
            )  # saving the coordinate data into a csv file
            writer.writerow(row)
            count = count + 1  # increase the data counter
            file.flush()
            sleep(8)  # take a picture every 8 seconds (+ ~2s time for taking the picture)
            remaining_time = max((end_time - datetime.now()), timedelta(0))
            print(f"Remaining time: {remaining_time}")
        else:
            print("In darkness, starting loop again")
        sleep(0)

print("Timer ended, program stopped" if not enough_time else "No more space left, program stopped")
print(f"{count} pictures taken")
print(f"Space used: {get_remaining_space(base_folder)} GB")
print(f"Runtime: {datetime.now() - start_time}")
# Program end
