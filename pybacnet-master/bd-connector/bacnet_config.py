"""
    bacnet-config.py
    ~~~~~~~~~~~~~~

    BACnet configuration file. Contains information specific to bacnet such as building to
    devices mapping, which properties provide important descriptions, building-depot
    dataservice to be used, etc.

    @copyright:	(c) 2014 SynergyLabs
    @license:	UCSD License. See License file for details.
    @authors: bbalaji@ucsd.edu
"""
# Note: Should have a different config file for every campus

# bacnet connector configuration dictionary
config = {"bacnet_priority": 9, #Priority given by UCSD Facilities Management
          "institution": "UCSD",
          "campus": "Main",
          "buildings":{
                        "EBU3B": {
                            "bacnet_devices": ["505","506"],
                            "device_desc_prop": "bacnet.PROP_DESCRIPTION",
                            "object_sensor_type":"bacnet.PROP_DESCRIPTION",
                            "object_desc_prop": "PROP_JCI_NAME",
                            "split_symbol": ".",
                            "split_names": ["building","room","empty","sensor_abrev"],
                            "bd_dataservice_url":"https://bd-datas1.ucsd.edu",
                            "bd_username": "bacnet_connector@ob-ucsd-cse.ucsd.edu",
                            "bd_api_key": "84a96fad-1aa7-4c05-aeeb-286b781584b0",
                            }
                    }
        }