"""
    bd-bacnet.py
    ~~~~~~~~~~~~~~

    The main file for the bacnet connector for BuildingDepot

    @copyright:	(c) 2014 SynergyLabs
    @license:	UCSD License. See License file for details.
    @authors: bbalaji@ucsd.edu
"""
import os
import sys
from operator import itemgetter
import bacnet
import optparse
import json
import shelve
from building_depot import DataService, BDError
from datetime import datetime
from discover import discover_bacnet_devices, discover_device_objects
from optparse import OptionParser
from bacnet_config import config
import logging
from read_write import ReadWrite

#Parse arguments
parser = OptionParser()
parser.add_option("-l", "--logfile", dest="log_file",
                  help="File for bacnet connector logs. Default: bd_connector.log",
                  metavar="FILE", default="bd_connector.log")
parser.add_option("-d", "--discover", dest="discover_sensors",
                  help="Discover bacnet devices and objects as specified in config. \
                  Default: False", default=False, metavar="BOOL")
parser.add_option("-c", "--clear_cache", dest="clear_cache",
                  help="Clear sensor uuid cache to get uuid directly from \
                       BuildingDepot. Default: False", default=False, metavar="BOOL")
parser.add_option("-s", "--clear_subscriber_changes",
                 dest="clear_subscriber_changes",
                 help="Clear subscription changes from BuildingDepot apps. \
                      Default: False", default=False, metavar="BOOL")
#TODO: Add cmd line for logging detail
#TODO: Add cmd line for cache clear

def main():
    #Parse arguments   
    (options, args) = parser.parse_args()

    #Initialize logging
    logging.basicConfig(filename=options.log_file,
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M:%S',
                        level=logging.INFO) #make debug cmd line param
    requests_log = logging.getLogger("requests")
    requests_log.setLevel(logging.WARNING)
    
    # Note: Must use default port for whois
    bacnet.Init(None, None)
    logging.info("Initialized BACnet")

    if options.clear_cache:
        os.remove("sensor_uuid.db")

    if options.discover_sensors:
        os.remove("bacnet_devices.db")
        discover_bacnet_devices()
    
    #TODO: Do the read-write for all buildings.
    #Possibly using threads.
    
    #for building in config["buildings"]    
    cse_dict = config["buildings"]["EBU3B"]
    #Warning: hard coding CSE NAEs for now
    #TODO: Automatically infer building related information from bacnet data
    cse_devices = cse_dict["bacnet_devices"]
    #Warning: hard coding CSE dataservice for now. Will need a way to discover this.
    #TODO: Automatically populate dataservice url
    cse_dataservice_url = cse_dict["bd_dataservice_url"]
    bd_username = cse_dict["bd_username"]
    bd_api_key = cse_dict["bd_api_key"]
    #bd_username = "admin@testbd.org"
    #bd_api_key = "b29c4bde-b453-48fc-881c-5af0d5cc83a4"
    building_depot_priority = config["bacnet_priority"]
    
    if options.discover_sensors:
        discover_device_objects(cse_devices)
    #exit after discovery
    #sys.exit()
    
    #Initialize BuildingDepot Dataservice
    bacnet_dataservice = DataService(cse_dataservice_url, bd_api_key, bd_username)
    
    if options.clear_subscriber_changes:
        bacnet_dataservice.clear_subscriber_changes(bd_username)
    
    #Open dictionary with saved device list and info
    bacnet_devices_dict = shelve.open('bacnet_devices.db', 'r')
    
    #Initialize read write object
    read_write_sensor = ReadWrite(bacnet_dataservice, "EBU3B")
    
    while True:
        for device_name in cse_devices:
            device = bacnet_devices_dict[device_name]
            h_dev = device['props']
            for sensor_obj in device['objs']:
                #Read current value
                read_write_sensor.batch_read_bacnet(sensor_obj, h_dev)
                #Write values from buildingdepot
                read_write_sensor.write_bacnet(bacnet_devices_dict)
                
        logging.info("Read all BACnet sensors for building %s", "EBU3B")
    bacnet_devices_dict.close()
    

if __name__ == "__main__":
  main()
