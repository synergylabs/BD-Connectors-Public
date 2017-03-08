#/usr/bin/python
import logging
from building_depot import DataService, BDError
import urllib

cse_dataservice_url = "https://bd-datas1.ucsd.edu"
bd_username = "admin@testbd.org"
bd_api_key = "b29c4bde-b453-48fc-881c-5af0d5cc83a4"
building_depot_priority = 9 #Priority given by UCSD Facilities Management

bd_username = "bacnet_connector@ob-ucsd-cse.ucsd.edu"
bd_api_key = "84a96fad-1aa7-4c05-aeeb-286b781584b0"

#Connect with BuildingDepot
bacnet_dataservice = DataService(cse_dataservice_url, bd_api_key, bd_username)

#print bacnet_dataservice.list_subscriber_changes(bd_username)
#print bacnet_dataservice.clear_subscriber_changes(bd_username)

#print bacnet_dataservice.view_sensor_template('Zone Temperature')
#source_identifier = "505_0_3000144"
#print bacnet_dataservice.list_sensors({'source_identifier': source_identifier})

logging.basicConfig(level=logging.INFO)

#Creating sensorpoints for wall sensor template
try:
    #Main HW RETURN TEMP
    sensor_uuid = "9f1164fc-74c7-11e2-b454-00163e005319"
    data = {
        "source name": "MAIN HW RETURN TEMP EBU3B HW-SYS",
        "source_identifier": "505_0_3000003",
    }

#    response = bacnet_dataservice.create_sensorpoint_type(**data)
    template = 'Warm Cool Adjust'
#    template = urllib.quote_plus(template)
    print template
    response = bacnet_dataservice.update_sensor(sensor_uuid, **data)
    print response
except BDError as e:
    print e
