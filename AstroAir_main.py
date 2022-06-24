#imports


from sense_hat import SenseHat
from datetime import datetime, timedelta
import time
import csv
from pathlib import Path
from logzero import logger, logfile
from gpiozero import MotionSensor

sense = SenseHat()
sense.low_light = True

#setup


#setup for the base_faolder for the data-csv and the log file

base_folder = Path(__file__).parent.resolve()   # to get the right path without using a certain path
data_file = base_folder/'data.csv'  # declares which file the data needs to be written in
logfile(base_folder/'events.log')

#setup for the motion detector

pir = MotionSensor(pin=12)

#variables


#mean values

meantemp = 0
meanpressure = 0
meanhumidity = 0

tempcounter = 0
pressurecounter = 0
humiditycounter = 0

tempmean = 0
humiditymean = 0
pressuremean = 0

#target values representing optimal air quality

target_temp = 22
target_pressure = 1013
target_humidity = 60

G = (0, 128, 9)
Y = (128, 128, 0)
R = (128, 0, 0)
O = (0,0,0)

#pixel colours

#pressure (green)
green = (0, 128, 0)

#temperature (red)

red = (128, 0, 0)

#humidity (blue)

blue = (0, 0, 128)

#none (white)

white = (128, 128, 128)

#bad smiley

red_led = [
   O, O, O, O, O, O, O, O,
   O, R, R, O, O, R, R, O,
   O, R, R, O, O, R, R, O,
   O, O, O, O, O, O, O, O,
   O, O, O, O, O, O, O, O,
   O, O, R, R, R, R, O, O,
   O, R, O, O, O, O, R, O,
   R, O, O, O, O, O, O, R,
   ]

#neutral smiley

yellow_led = [
   O, O, O, O, O, O, O, O,
   O, Y, Y, O, O, Y, Y, O,
   O, Y, Y, O, O, Y, Y, O,
   O, O, O, O, O, O, O, O,
   O, O, O, O, O, O, O, O,
   Y, Y, Y, Y, Y, Y, Y, Y,
   O, O, O, O, O, O, O, O,
   O, O, O, O, O, O, O, O,
   ]

#happy smiley

green_led = [
   O, O, O, O, O, O, O, O,
   O, G, G, O, O, G, G, O,
   O, G, G, O, O, G, G, O,
   O, O, O, O, O, O, O, O,
   O, G, O, O, O, O, G, O,
   O, G, O, O, O, O, G, O,
   O, O, G, O, O, G, O, O,
   O, O, O, G, G, O, O, O,
   ]

#functions


#update screen according to measurements from sensors and represent them scaled to the 64 - pixel frame

def update_screen(mode):
  if mode == "temp":
    temp = sense.temp
    temp_value = (temp - 10)/ 0.3125
    pixels = [red if i < temp_value else white for i in range(64)]

  elif mode == "pressure":
    pressure = sense.pressure
    pressure_value = (pressure - 900) / 3.125
    pixels = [green if i < pressure_value else white for i in range(64)]

  elif mode == "humidity":
    humidity = sense.humidity
    humidity_value = 64 * humidity / 100
    pixels = [blue if i < humidity_value else white for i in range(64)]

  sense.set_pixels(pixels)


#difference between values function

def diff(value_wanted, value_measured):
  
  if value_wanted > value_measured:
    diff = value_wanted - value_measured
  elif value_wanted < value_measured:
    diff = value_measured - value_wanted
  else:
    diff = 0
    
  return diff

#show according happy, neutral, bad smileys function (greater difference between target and measured value roughly corresponds to worse air quality)

#for temp

def smiley_temp(target, measured):
  if diff(target, measured) < 1:
    sense.set_pixels(green_led)
  
  elif 3 > diff(target, measured) > 1:
    sense.set_pixels(yellow_led)
  
  elif diff(target, measured) > 3:
    sense.set_pixels(red_led)
    
  time.sleep(1)
  
#for pressure

def smiley_pressure(target, measured):
  if diff(target, measured) < 5:
    sense.set_pixels(green_led)
  
  elif 11 > diff(target, measured) > 5:
    sense.set_pixels(yellow_led)
  
  elif diff(target, measured) > 11:
    sense.set_pixels(red_led)
    
  time.sleep(1)
  
#for humidity

def smiley_humidity(target, measured):
  if diff(target, measured) < 10:
    sense.set_pixels(green_led)
  
  elif 30 > diff(target, measured) > 10:
    sense.set_pixels(yellow_led)
  
  elif diff(target, measured) > 30:
    sense.set_pixels(red_led)
    
  time.sleep(1)
  
#create a csv file for the measured data
  
def create_csv(data_file):
    with open(data_file, 'w') as f:
        writer = csv.writer(f)
        header = ("Date/time", "Temperature", "Humidity", "Pressure", "Motion")
        writer.writerow(header)
        
#add data to the csv file

def add_csv_data(data_file, data):
    with open(data_file, 'a') as f:
        writer = csv.writer(f)
        writer.writerow(data)

#main loop
        
        
#call the function to create a csv file
        
create_csv(data_file) 

#time setup: Create a datetime variable to store the start time

start_time = datetime.now()

#Create a datetime variable to store the current time

now_time = datetime.now()

#show measured sonsor data and smileys for temperature, pressure, humidity until 3 hours have elapsed

while (now_time < start_time + timedelta(minutes=179)):

  try:
      update_screen("temp")
      time.sleep(1)
      smiley_temp(target_temp, sense.temp)
      print ("Motion: ", pir.motion_detected) #repeated motion detection: values of pir.motion_detect are True or False depending on the Output of the Sensor. These values are to be stored in the csv file and compared to the other data after the experiment
      update_screen("pressure")
      time.sleep(1)
      smiley_pressure(target_pressure, sense.pressure)
      print ("Motion: ", pir.motion_detected)
      update_screen("humidity")
      time.sleep(1)
      smiley_humidity(target_humidity, sense.humidity)
      print ("Motion: ", pir.motion_detected)
      
      now_time = datetime.now() #time now, used for the 3 hour counter
      
      logger.info(f'New line started') #each stored line will be stored into the logfile
      row = (datetime.now(), sense.temperature, sense.humidity, sense.pressure, pir.motion_detected)
      add_csv_data(data_file, row)
      
      meantemp = meantemp + sense.temperature
      tempcounter += 1
      meanpressure = meanpressure + sense.pressure
      pressurecounter += 1
      meanhumidity = meanhumidity + sense.humidity
      humiditycounter += 1

#exception for the main loop will be stored into the logfile

  except Exception as e:
      logger.error(f'{e.__class__.__name__}: {e}')
      
sense.show_letter("E", back_colour = red)
time.sleep(1)
sense.show_letter("X", back_colour = red)
time.sleep(1)
sense.show_letter("P", back_colour = red)
time.sleep(1)
sense.show_letter("E", back_colour = red)
time.sleep(1)
sense.show_letter("R", back_colour = red)
time.sleep(1)
sense.show_letter("I", back_colour = red)
time.sleep(1)
sense.show_letter("M", back_colour = red)
time.sleep(1)
sense.show_letter("E", back_colour = red)
time.sleep(1)
sense.show_letter("N", back_colour = red)
time.sleep(1)
sense.show_letter("T", back_colour = red)
time.sleep(2)
sense.show_letter("E", back_colour = red)
time.sleep(1)
sense.show_letter("N", back_colour = red)
time.sleep(1)
sense.show_letter("D", back_colour = red)
time.sleep(1)
sense.show_letter("E", back_colour = red)
time.sleep(1)
sense.show_letter("D", back_colour = red)
sense.clear()

#create average values

tempmean = meantemp/tempcounter
pressuremean = meanpressure/pressurecounter
humiditymean = meanhumidity/humiditycounter

row = ('Mean Values', 'Temperature', 'Humidity', 'Pressure')
add_csv_data(data_file, row)
row = ('', tempmean, humiditymean, pressuremean)
add_csv_data(data_file, row)

logger.info(f'Experiment ended')
