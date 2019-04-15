#!/usr/bin/env python

'''
 ' Moisture sensing and watering routine for Farmbot
'''

import os, sys, json, Qualify
from random import randint
from farmware_tools import device, app, get_config_value
from Coordinate import Coordinate

def take_readings():
	plants_chosen = []
	device.execute(moisture_tool_retrieve_sequence_id)
	#coord = Coordinate(device.get_current_position('x'), device.get_current_position('y'), Z_TRANSLATE)
	bot = Coordinate(device.get_current_position('x'), device.get_current_position('y'))
	for i in range(NUM_SITES):
		rand_plant_num = randint(0, len(target_plants) - 1)
		while rand_plant_num in plants_chosen:
			rand_plant_num = randint(0, len(target_plants) - 1)
		plants_chosen.append(rand_plant_num)
		rand_plant = plants[rand_plant_num]
		device.log(json.dumps(rand_plant))
		bot.set_coordinate(z=Z_TRANSLATE)
		#coord.set_coordinate(rand_plant['x'], rand_plant['y'], Z_TRANSLATE)
		bot.set_coordinate(rand_plant['x'], rand_plant['y'], move_abs=False)	# set the plant coordinate, auto-move disabled
		bot.set_offset(OFFSET_X, OFFSET_Y)										# set the offset, auto-move enabled
		bot.set_axis_position('z', SENSOR_Z_DEPTH)								# plunge sensor into soil, auto-move enabled
		# take reading(s)
		site_readings = []
		for j in range(NUM_SAMPLES):
			device.read_pin(PIN_SENSOR, 'Sensor', 1)
			site_readings.append(device.get_pin_value(PIN_SENSOR))
			device.wait(100)
		average = 0
		for reading in site_readings:
			average += reading
		average /= NUM_SAMPLES
		moisture_readings.append(average)
		device.log('Site Reading #{}: {}'.format(i, average), 'success')
	device.log('Readings: {}'.format(json.dumps(moisture_readings)), 'success')
	device.execute(moisture_tool_return_sequence_id)

def response():
	average = 0
	for i in moisture_readings:
		average += i
	average /= len(moisture_readings)
	device.log('Total Moisture Average: {}'.format(average), 'info')
	if average < THRESHOLD:
		device.execute(water_tool_retrieve_sequence_id)
		device.execute(water_sequence_id)
		device.execute(water_tool_return_sequence_id)

PIN_LIGHTS = 7
PIN_SENSOR = 59
PIN_WATER = 8
PKG = 'Water Routine'

input_errors = []

PLANT_TYPES = Qualify.get_csv(PKG, 'plant_types')
SENSOR_Z_DEPTH = Qualify.interger(PKG, 'sensor_z_depth')
Z_TRANSLATE = Qualify.interger(PKG,'z_translate')
OFFSET_X = Qualify.interger(PKG,'offset_x')
OFFSET_Y = Qualify.interger(PKG,'offset_y')
THRESHOLD = Qualify.interger(PKG,'threshold')
NUM_SITES = Qualify.interger(PKG,'num_sites')
NUM_SAMPLES = Qualify.interger(PKG,'num_samples')

moisture_tool_retrieve_sequence_id = Qualify.Sequence(PKG, 'tool_moisture_retrieve')
moisture_tool_return_sequence_id = Qualify.Sequence(PKG, 'tool_moisture_return')
water_tool_retrieve_sequence_id = Qualify.Sequence(PKG, 'tool_water_retrieve')
water_tool_return_sequence_id = Qualify.Sequence(PKG, 'tool_water_return')
water_sequence_id = Qualify.Sequence(PKG, 'water_sequence')

moisture_readings = []

if len(input_errors):
	for err in input_errors:
		device.log(err, 'warn')
	device.log('Fatal errors occured, farmware exiting.', 'warn')
	sys.exit()

if device.get_current_position('x') > 10 or device.get_current_position('y') > 10 or device.get_current_position('z') < -10:
	device.home('all')

device.log('Read Pin: {}'.format(device.read_pin(PIN_SENSOR, 'Sensor', 1)))

device.write_pin(PIN_LIGHTS, 1, 0)

target_plants = []
all_plants = app.get_plants()
for plant in all_plants:
	if plant['name'].lower in PLANT_TYPES:
		target_plants.append(plant)

take_readings()
response();

device.home('all')
device.write_pin(PIN_LIGHTS, 0, 0)
