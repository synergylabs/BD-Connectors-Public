"""
    bd_create.py
    ~~~~~~~~~~~~~~

    Code responsible for reading and writing sensor values between BACnet and
    BuildingDepot.

    @copyright:	(c) 2014 SynergyLabs
    @license:	UCSD License. See License file for details.
    @authors: bbalaji@ucsd.edu
"""
import shelve
from bacnet_config import config
from bd_create import BDCreate
import bacnet
import logging
from datetime import datetime
from dateutil.tz import tzutc, tzlocal
import sys
from building_depot import BDError
import requests

class ReadWrite(object):
    def __init__(self, dataservice, building, uuid_file = 'sensor_uuid.db'):
        self.dataservice = dataservice
        self.building = building
        self.uuid_dict = shelve.open(uuid_file)
        self.sensor_maker = BDCreate(self.dataservice, self.building)
        self.bacnet_priority = config["bacnet_priority"]
        self.datapoints = []
        self.batch_count = 10
        logging.info("Warning: Only reading values from "
                     "analog, binary and multistate sensors")

    def get_sensor_uuid(self, source_identifier, sensor_obj, sensorpoint_type):
        #Check if uuid mapping exists in cached dictionary
        if source_identifier in self.uuid_dict:
            sensor_uuid = self.uuid_dict[source_identifier]
            return sensor_uuid
            #print "cache:", sensor_uuid
        else:
            query_context = {'source_identifier': source_identifier}
            try:
                response = self.dataservice.list_sensors(query_context)
            except (BDError, requests.exceptions.RequestException):
                e = sys.exc_info()
                logging.error("Could not get list of sensors by context. Error %s, %s", e[0], e[1])
                return None    
            if len(response['sensors']) == 1: #unique sensor found
                sensor_uuid = response['sensors'][0]['uuid'] 
                self.uuid_dict[source_identifier] = sensor_uuid #cache the uuid
                print "context:", sensor_uuid
            elif len(response['sensors']) == 0: #need to create sensor
                #if sensor doesn't exist, create it in building depot
                try:
                    sensor_uuid = self.sensor_maker.create_bd_entities(
                        source_identifier, sensor_obj, sensorpoint_type)
                    logging.info("Created sensor entities for %s", source_identifier)
                except (BDError, requests.exceptions.RequestException):
                    e = sys.exc_info()
                    logging.error("Could not create sensor entities %s. Error %s, %s",
                                  source_identifier, e[0], e[1])
                    return None
                self.uuid_dict[source_identifier] = sensor_uuid
                return sensor_uuid
            else: #more than one sensor found
                logging.error("More than one instance of sensor found - %s", source_identifier)
                return None
    
    def read_bacnet(self, sensor_obj, h_dev, sensorpoint_type = 'PresentValue'):
        #TODO: Implement batch read
        #Read current value
        h_obj = sensor_obj['props']
        #Read values only from analog, binary and multistate sensors
        if h_obj['type'] not in (0,1,2,3,4,5,14):
            logging.debug("Not reading present value from sensor %s %s %s",
                         h_dev['device_id'], h_obj['type'], h_obj['instance'])
            return False
        try:
            current_value = bacnet.read_prop(h_dev, h_obj['type'], h_obj['instance'],
                                             bacnet.PROP_PRESENT_VALUE, -1)    
        except IOError as e:
            current_value = None
            logging.error("Could not read sensor: %s, %s, %s. Error %s", h_dev['device_id'],
                          h_obj['type'], h_obj['instance'], e)
            return False
        
        source_identifier = str(h_dev['device_id']) + '_' + str(h_obj['type']) \
                                    + '_' + str(h_obj['instance'])
        sensor_uuid = self.get_sensor_uuid(source_identifier, sensor_obj, sensorpoint_type)
        if sensor_uuid is None:
            return False
        
        current_time = datetime.now(tzlocal()).isoformat()
        datapoint = [{current_time: current_value}]
       
        try:
            response = self.dataservice.put_timeseries_datapoints(
                                sensor_uuid, sensorpoint_type, datapoint)
            #pass
        except (BDError, requests.exceptions.RequestException):
            e = sys.exc_info()
            logging.error("Could not put data in timeseries. Error %s, %s", e[0], e[1])
            return False
        logging.debug("Posting to sensor %s with value %s", source_identifier, current_value)
        #print response
        return True

    def batch_read_bacnet(self, sensor_obj, h_dev, sensorpoint_type = 'PresentValue'):
        #TODO: Implement batch read
        #Read current value
        h_obj = sensor_obj['props']
        #Read values only from analog, binary and multistate sensors
        if h_obj['type'] not in (0,1,2,3,4,5,14):
            logging.debug("Not reading present value from sensor %s %s %s",
                         h_dev['device_id'], h_obj['type'], h_obj['instance'])
            return False
        try:
            current_value = bacnet.read_prop(h_dev, h_obj['type'], h_obj['instance'],
                                             bacnet.PROP_PRESENT_VALUE, -1)
        except IOError as e:
            current_value = None
            logging.error("Could not read sensor: %s, %s, %s. Error %s", h_dev['device_id'],
                          h_obj['type'], h_obj['instance'], e)
            return False
        
        source_identifier = str(h_dev['device_id']) + '_' + str(h_obj['type']) \
                                    + '_' + str(h_obj['instance'])
        sensor_uuid = self.get_sensor_uuid(source_identifier, sensor_obj, sensorpoint_type)
        if sensor_uuid is None:
            return False
            
        current_time = datetime.now(tzlocal()).isoformat()
        datapoint = [{current_time: current_value}]
        self.datapoints.append({'datapoint': datapoint,
                                'sensor_uuid':sensor_uuid,
                                'sensorpoint':sensorpoint_type,
                            })
       
        if len(self.datapoints) >= self.batch_count:
            batch_datapoints = {}
            for data in self.datapoints:
                sensor_dict = {data['sensorpoint']: data['datapoint']}
                batch_datapoints[data['sensor_uuid']] = sensor_dict
            try:
                response = self.dataservice.put_timeseries_datapoints_batch(**batch_datapoints)
                logging.debug("Posted batch datapoints to building depot.")
                #print response
            except (BDError, requests.exceptions.RequestException):
                e = sys.exc_info()
                logging.error("Could not put batch data in timeseries. Error %s, %s", e[0], e[1])
                return False
            #logging.debug("Posting to sensor %s with value %s", source_identifier, current_value)
            #print response
            self.datapoints = []
            return True
        else:
            return True

    
    def write_bacnet(self, bacnet_devices_dict):
        #Check if there is anything to write
        bd_username = config["buildings"][self.building]["bd_username"]
        try:
            response = self.dataservice.list_subscriber_changes(bd_username) #user bacnet_dataservice.username instead.
        except (BDError, requests.exceptions.RequestException):
            e = sys.exc_info()
            logging.error("Could not get subscriber changes. Error %s, %s", e[0], e[1])
            return False
        #print 'subscription: ', response
        #TODO: Handle more than 1000 changes
        if len(response['changes']) > 0: #if there is something to write
            #get the sensorpoint list to be written
            write_sensor_list = response['changes']
            #clear subscriber changes
            try:
                response = self.dataservice.clear_subscriber_changes(bd_username)
            except (BDError, requests.exceptions.RequestException):
                e = sys.exc_info()
                logging.error("Could not clear subscriber changes. Error %s, %s", e[0], e[1])
            #write to bacnet
            for write_sensor in write_sensor_list:
                #get the latest datapoint
                try:
                    response = self.dataservice.get_latest_timeseries_datapoint(write_sensor['sensor_uuid'],
                                                                                write_sensor['sensorpoint'])
                except (BDError, requests.exceptions.RequestException):
                    e = sys.exc_info()
                    logging.error("Could not get latest timeseries for sensor %s. Error %s, %s",
                                  write_sensor['sensor_uuid'], e[0], e[1])
                    continue
                datapoint = response['timeseries'][0] #should only contain one value
                for key, value in datapoint.iteritems():
                    data_value = value
                
                #get the source identifier of the sensor
                response = self.dataservice.view_sensor(write_sensor['sensor_uuid'])
                source_identifier = response['source_identifier']
                object_device_id, object_type, object_instance = source_identifier.split('_')
                write_dev = bacnet_devices_dict[str(object_device_id)]["props"]
                object_device_id = int(object_device_id)
                object_type = int(object_type)
                object_instance = int(object_instance)
                #Warning: hard coding object property
                object_property = bacnet.PROP_PRESENT_VALUE
                #get property tag
                if data_value == -1: #relinquish control
                    data_value = 0
                    property_tag = 0 #TODO: change to bacnet constant name
                elif object_type == 1: #analog object, float values
                    property_tag = 4
                elif object_type == 4: #binary object, boolean values
                    property_tag = 1
                elif object_type == 14: #multi-state object, int values
                    property_tag = 2
                else: #should not receive
                    logging.error("Error: incorrect data written by BuildingDepot")
                    return False
                print "Writing:", type(data_value), data_value, str(data_value), source_identifier
                try:
                    write_response = bacnet.write_prop(write_dev, object_type, object_instance, bacnet.PROP_PRESENT_VALUE, 
                                                    property_tag, str(data_value), self.bacnet_priority)
                    logging.info("Writing to sensor %s %s %s with value: %s", object_device_id,
                             object_type, object_instance, data_value)
                except IOError as e:
                    logging.error("Could not write to sensor %s %s %s with value %s",
                                  object_device_id, object_type, object_instance, data_value)
                    return False
                
                return True
        else:
            logging.debug("Nothing to write to BACnet")