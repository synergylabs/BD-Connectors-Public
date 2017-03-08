"""
    bd_create.py
    ~~~~~~~~~~~~~~

    Code responsible for creating relevant BuildingDepot entities for bacnet
    connector - sensor templates, sensorpoint types, sensors, keywords, etc.

    @copyright:	(c) 2014 SynergyLabs
    @license:	UCSD License. See License file for details.
    @authors: bbalaji@ucsd.edu
"""
from bacnet_config import config
from util import *
import sys
import logging
from building_depot import DataService, BDError
import re

class BDCreate(object):
    #Create new instance for every building
    def __init__(self, bd_dataservice, building):
        self.dataservice = bd_dataservice
        self.institution = config["institution"]
        self.campus = config["campus"]
        self.building = building 
        self.config = config["buildings"][building]
        self.sensor_network = "BACNET"
        
    def create_sensorpoint_type(self, type_name = "PresentValue"):
        #TODO: Deal with other types of sensorpoints such as operator
        #override
        #Check if sensorpoint type exists first
        type_name = re.sub('[^a-zA-Z0-9_]', ' ', type_name)
        try:
            self.dataservice.view_sensorpoint_type(type_name)
            return
        except:
            e = sys.exc_info()
            logging.error("Could not locate sensorpoint %s. Error %s, %s",
                          type_name, e[0], e[1])
            #pass
        
        data = {
            "name": type_name,
            "description": "Shows the present value of sensor in BACnet",
            "data_type": "float", #Warning: there should be no data type.
                                  #Assuming float for now
        }
        try:
            response = self.dataservice.create_sensorpoint_type(**data)
            logging.info("Created sensorpoint type: " + str(response))
        except:
            e = sys.exc_info()
            logging.error("Could not create sensorpoint %s. Error %s, %s",
                          type_name, e[0], e[1])
            raise
            

    def create_sensor_template(self, sensor_template, sensorpoint_type = 'PresentValue'):
        #Check if sensor template exists first
        sensor_template = re.sub('[^a-zA-Z0-9_]', ' ', sensor_template)
        try:
            self.dataservice.view_sensor_template(sensor_template)
            return
        except:
            e = sys.exc_info()
            logging.info("Could not locate sensor template %s. Error %s %s",
                         sensor_template, e[0], e[1])
            pass
        
        template_data = {
            "name": sensor_template,
            "description": "BACnet Sensor",
            "sensorpoint_types":[sensorpoint_type]
        }
        try:
            response = self.dataservice.create_sensor_template(**template_data)
            logging.info("Created sensor template: "+str(response))
        except:
            e = sys.exc_info()
            logging.error("Could not create sensor template %s. Error %s, %s",
                          sensor_template, e[0], e[1])
            raise
    
    def add_sensorpoint_type(self, sensor_template, sensorpoint_type = 'PresentValue'):
        sensor_template = re.sub('[^a-zA-Z0-9_]', ' ', sensor_template)
        sensorpoint_type = re.sub('[^a-zA-Z0-9_]', ' ', sensorpoint_type)
        try:
            response = self.dataservice.view_sensor_template(sensor_template)
            if 'sensorpoint_types' in response:
                sensorpoint_type_dict = {spt['name']: spt['description'] 
                                            for spt in response['sensorpoint_types']}
                if sensorpoint_type not in sensorpoint_type_dict:
                    logging.info("%s sensorpoint type not in sensor template", sensorpoint_type)
                else:
                    return
            else:
                logging.info("%s sensorpoint type not in sensor template", sensorpoint_type)
        except:
            e = sys.exc_info()
            logging.error("Could not access sensorpoint_type %s. Error %s, %s",
                          sensorpoint_type, e[0], e[1])
            pass
        try:
            response = self.dataservice.add_sensor_template_sensorpoint_type(sensor_template,
                                                                 sensorpoint_type)
            logging.info("Added sensorpoint type %s to sensor template %s",
                         sensorpoint_type, sensor_template)
        except:
            e = sys.exc_info()
            logging.error("Could not add sensorpoint type %s to sensor template %s. Error %s, %s",
                          sensorpoint_type, sensor_template, e[0], e[1])
            raise
        
    def create_sensor_network(self, network_name='BACNET'):
        network_name = re.sub('[^a-zA-Z0-9_]', ' ', network_name)
        try:
            self.dataservice.view_sensor_network(network_name)
            return
        except:
            e = sys.exc_info()
            logging.error("Could not access network %s. Error %s, %s", network_name, e[0], e[1])
            pass
        network_data = {
            "name": network_name,
            "description": "BACnet network used by Building Management Systems"
        }
        try:
            response = self.dataservice.create_sensor_network(**network_data)
            logging.info("Created sensor network: %s", response)
        except:
            e = sys.exc_info()
            logging.error("Could not create sensor network %s. Error %s, %s",
                          network_name, e[0], e[1])
            raise

    def create_keyword(self, keyword = "system"):
        system = re.sub('[^a-zA-Z0-9_]', ' ', keyword)
        try:
            self.dataservice.view_keyword(keyword)
            return
        except:
            pass
        keyword_data = {
            "name": keyword,
            "description": "Part of building system"
        }
        try:
            response = self.dataservice.create_keyword(**keyword_data)
            logging.info("Created keyword: "+str(response))
        except:
            e = sys.exc_info()
            logging.error("Could not create keyword: %s. Error %s, %s",
                          keyword, e[0], e[1])
            raise
            
    def create_sensor(self, source_identifier, sensor_obj):
        sensor_type = sensor_obj["sensor_type"]
        sensor_type = (re.sub('[^a-zA-Z0-9_]', ' ', sensor_type)).strip()
        sensor_name = ("%s %s" % (sensor_type, self.building) )
        #Getting sensor context
        sensor_context = {
                    "institution": self.institution,
                    "campus": self.campus,
                    "building": self.building,
            }
        context_string = sensor_obj["object_desc_prop"]
        split_symbol = self.config["split_symbol"]
        split_names = self.config["split_names"]
        
        try:
            split_contexts = context_string.split(split_symbol)
        except ValueError as e:
            logging.error("Could not split sensor %s, with context %s. %s",
                          sensor_type, context_string, e)
            raise
        # Note: May need to revisit this. Too hard coded still
        split_context_dict = {}
        for index, context in enumerate(split_contexts):
            name = split_names[index]
            split_context_dict[name] = context
        
        logging.info("Split context: %s. Sensor type: %s",
                     split_context_dict, sensor_type)
        if "room" in split_context_dict:
            system = split_context_dict["room"]
            if contains_digits(system):
                room = system
                if room[3] == 'B': #hard coded
                    floor = 'Basement'
                else:
                    floor = 'Flr-' + room[3] #hard coded
                sensor_context["room"] = room
                sensor_context["floor"] = floor
                sensor_name = sensor_name + " " + room
            else:
                sensor_context["system"] = system
                sensor_name = sensor_name + " " + system
        
        
        ##Special case for handling Soft Thermostat. Update Source Identifier.
        if sensor_type == "Warm Cool Adjust":
            sensor_context["template"]=sensor_type
            try:
                response = self.dataservice.list_sensors(sensor_context)
            except:
                e = sys.exc_info()
                logging.error("Could not find sensor: %s. Error %s, %s",
                              sensor_name, e[0], e[1])
                return
            if len(response['sensors']) > 0: #sensor found
                sensor_uuid = response['sensors'][0]['uuid']
                update_data = {
                    'source_name': sensor_name,
                    'source_identifier': source_identifier,
                }
                try:
                    self.dataservice.update_sensor(sensor_uuid, **update_data)
                    logging.info("Updating sensor: %s", sensor_name)
                    return sensor_uuid
                except:
                    e = sys.exc_info()
                    logging.error("Could not update sensor: %s. Error %s, %s",
                                  sensor_name, e[0], e[1])
                    return
            else:
                logging.info("No sensor found. Response: %s", response['sensors'])
                del sensor_context["template"]
        
        ## Create sensor (name, source id, template, network, context - institution, campus, building, floor, room)
        sensor_data = {
                "source_name": sensor_name,
                "source_identifier": source_identifier,
                "template": sensor_type,
                "network": self.sensor_network,
                "context": sensor_context,
        }
        try:
            response = self.dataservice.create_sensor(**sensor_data)
            logging.info("Created sensor: "+str(response))
            return response
        except:
            e = sys.exc_info()
            logging.error("Could not create sensor: %s. Error %s, %s",
                          sensor_name, e[0], e[1])
            raise

    
    def create_bd_entities(self, source_identifier, sensor_obj, sensorpoint_type):
        '''Deal with all the different types of entities that need to
            be created - sensor, sensorpoint, sensor template, etc.
        '''
        try:
            #Steps for creating a sensor
            ## Create sensorpoint type if necessary
            self.create_sensorpoint_type()
            ## Create sensor template if necessary
            self.create_sensor_template(sensor_obj["sensor_type"])
            ## Add sensorpoint type to template if necessary
            self.add_sensorpoint_type(sensor_obj["sensor_type"])
            ## Use BACnet sensor network. Create if necessary
            self.create_sensor_network()
            ## Create keyword if necessary - room, floor, system, etc.
            self.create_keyword()
            ## Create sensor
            sensor_uuid = self.create_sensor(source_identifier, sensor_obj)
            return sensor_uuid
        except:
            e = sys.exc_info()
            logging.error("Could not create sensor %s. Error %s, %s",
                          sensor_obj, e[0], e[1])
            raise

