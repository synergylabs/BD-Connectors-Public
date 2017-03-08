"""
    discover.py
    ~~~~~~~~~~~~~~

    Discover all bacnet devices and its device objects. Store in
    shelve dictionary.

    @copyright:	(c) 2014 SynergyLabs
    @license:	UCSD License. See License file for details.
    @authors: bbalaji@ucsd.edu
"""
import shelve
import bacnet
import logging
from operator import itemgetter
import re

#JCI = Johnson Control Inc. Using a proprietary object property defined by them.
#TODO: Define this in the bacenum.h file
PROP_JCI_NAME = 2390
#TODO: Discover vendor names, and use their proprietary tags

#Discover all the devices connected to the network. Store their details in a shelve dictionary
def discover_bacnet_devices():
    bacnet_devices_dict = shelve.open('bacnet_devices.db')    
    device_list = []
    # Discover and store devices
    bacnet_devices = bacnet.whois(5)
    logging.info("Found %s devices", len(bacnet_devices))
    total_object_count = 0
    for h_dev in sorted(bacnet_devices, key=itemgetter('device_id')):
        logging.info("Looking up device: %s", h_dev['device_id'])
        objs = []
        try: 
            name = bacnet.read_prop(h_dev, bacnet.OBJECT_DEVICE, h_dev['device_id'], bacnet.PROP_OBJECT_NAME, -1)
            logging.info("Name: %s", name)
        except IOError as e:
            name = None
            logging.error("Could not read name. Error: %s", e)
        try:
            obj_count = bacnet.read_prop(h_dev, bacnet.OBJECT_DEVICE, h_dev['device_id'], bacnet.PROP_OBJECT_LIST, 0)
            logging.info("Object count: %s", obj_count)
            total_object_count += obj_count
        except IOError as e:
            obj_count = None
            logging.error("Could not get object count. Error: %s", e)
        try:
          desc = bacnet.read_prop(h_dev, bacnet.OBJECT_DEVICE, h_dev['device_id'], bacnet.PROP_DESCRIPTION, -1)
          logging.info("Description: %s", desc)
        except IOError:
            desc = None
            logging.error("Could not read description. Error: %s", e)
        try:
          device_desc_prop = bacnet.read_prop(h_dev, bacnet.OBJECT_DEVICE, h_dev['device_id'], bacnet.PROP_DESCRIPTION, -1)
          logging.info("Description: %s", device_desc_prop)
        except IOError:
            device_desc_prop = None
            logging.error("Could not get device description property. Error: %s", e)
        #JCI = Johnson Control Inc.
        try:
            jci_name = bacnet.read_prop(h_dev, bacnet.OBJECT_DEVICE, h_dev['device_id'], PROP_JCI_NAME, -1)
            logging.info("JCI Given Name: %s", jci_name)
        except IOError:
            jci_name = None
            logging.error("Could not read JCI Name. Error: %s", e)
        logging.info("Device: %s, Name: %s, Description: %s, Objects: %s", h_dev['device_id'], name, desc, obj_count)
        device = {
        'props': h_dev,
        'name': re.sub('[^a-zA-Z0-9_]', ' ', name),
        'desc': desc,
        'device_desc_prop': re.sub('[^a-zA-Z0-9_]', ' ', device_desc_prop),
        'jci_name': re.sub('[^a-zA-Z0-9_]', ' ', jci_name),
        'obj_count':obj_count,
        'objs': []
        }
        device_id = str(h_dev['device_id'])
        bacnet_devices_dict[device_id] = device
        device_list.append(device)
        if obj_count == 0:
          logging.error("No objects found: %s", device['device_id'])
        continue
    logging.info("Total number of objects: %s", total_object_count)
    bacnet_devices_dict.close()
    
def discover_device_objects(cse_devices):
    bacnet_devices_dict = shelve.open('bacnet_devices.db')
    #NAE level (or device level) discovery
    # Get object properties and names
    for device_name in cse_devices:
        device = bacnet_devices_dict[device_name]
        for i in range(1, device["obj_count"]+1):
            h_dev = device["props"]
            h_obj = bacnet.read_prop(h_dev, bacnet.OBJECT_DEVICE, h_dev['device_id'], bacnet.PROP_OBJECT_LIST, i)
            if h_obj == None:
              logging.error("Object not found: %s", i)
              continue
            try:
              name = bacnet.read_prop(h_dev, h_obj['type'], h_obj['instance'], bacnet.PROP_OBJECT_NAME, -1)
            except IOError:
              name = None
            try:
              desc = bacnet.read_prop(h_dev, h_obj['type'], h_obj['instance'], bacnet.PROP_DESCRIPTION, -1)
            except IOError:
              desc = None
            try:
              sensor_type = bacnet.read_prop(h_dev, h_obj['type'], h_obj['instance'], bacnet.PROP_DESCRIPTION, -1)
            except IOError:
              sensor_type = None
            try:
              unit = bacnet.read_prop(h_dev, h_obj['type'], h_obj['instance'], bacnet.PROP_UNITS, -1)
            except IOError:
              unit = None
            try:
              object_desc_prop = bacnet.read_prop(h_dev, h_obj['type'], h_obj['instance'], PROP_JCI_NAME, -1)
            except IOError:
              object_desc_prop = None
            logging.info("Instance: %s, Name: %s, Description: %s, Unit: %s, JCI Name: %s",
                         h_obj['instance'], name, desc, unit, object_desc_prop)
            device['objs'].append({
              'props': h_obj,
              'name': re.sub('[^a-zA-Z0-9_]', ' ', name),
              'desc': desc,
              'sensor_type':re.sub('[^a-zA-Z0-9_]', ' ', sensor_type),
              'unit': unit,
              'object_desc_prop':re.sub('[^a-zA-Z0-9_]', ' ', object_desc_prop),
              'data_type': h_obj['type'],
              })
            logging.info("%s has %s objects", device['name'], len(device['objs']))
        bacnet_devices_dict[device_name] = device
    #TODO: Create building depot sensors in the discovery process
    bacnet_devices_dict.close()  