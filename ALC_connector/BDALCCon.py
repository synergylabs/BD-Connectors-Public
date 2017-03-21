import sys
import traceback


from random import *
from py4j.java_gateway import JavaGateway,GatewayParameters
from datetime import datetime
import time,os,re,atexit
from signal import SIGTERM
import requests, json, time, random, threading
from pprint import pprint
from datetime import datetime, timedelta

# BD DataService Configuration
global client_id 
global client_secret 
global Ourl
global build
global atoken
def getOauthToken():
  global client_id
  global client_secret
  global Ourl
  global atoken
  url = Ourl+"oauth/access_token/client_id="+client_id+"/client_secret="+client_secret
  response = requests.get(url,verify=False).json()
  access_token = response["access_token"]
  atoken = access_token
  return access_token
def sensorlist(inputurl, vals, name):
  global atoken
  access_token=atoken
  header = {"Authorization": "bearer " + access_token, 'content-type':'application/json'}
  url = inputurl
  url1 = url+"api/search"

  data = {"data": {"Tags": ["Institution:" + vals[0], 'floor:'+vals[1], 'room:' + vals[2], +'ip:'+vals[3], 'networknumber:'+vals[4], 'address:'+vals[5], 'ObjectType'+vals[6], 'objectID:'+vals[7]}}

  #data = {"data": {"ID": ["BasicBD:"+name]}}
  response = requests.post(url1, headers = header,data =json.dumps(data), verify=False)
  try:
	response = response.json()
	return response
  except:
	atoken = getOauthToken()
	header = {"Authorization": "bearer " + atoken, 'content-type':'application/json'}
	response = requests.post(url1, headers = header, data=json.dumps(data), verify=False)
	return response.json()
  return response.json()

def post_building_tag(name, value):
  access_token= getOauthToken()
  header = {"Authorization": "bearer " + access_token, 'content-type':'application/json'}
  global Ourl
  global build
  url1 = Ourl+"api/building/"+build+"/tags"
  payload = {'data': {
        'name': name,
        'value': value,
        'parents':[]
    }}
  payload = json.dumps(payload)
  response = requests.post(url1, headers = header, data = payload,verify=False)
#  print response.json()
  return response.json()
  

def post_timeseries_data(URL, sensor, Values):
  global atoken
  access_token= atoken
  header = {"Authorization": "bearer " + access_token, 'content-type':'application/json'}
  global Ourl
  temp  = ""
  count = 0
  for char in Ourl:
        if(count == len(Ourl)-2):
		temp+="2"
 	else:
		temp = temp+char
	count+=1
  
  url1 = temp+"api/sensor/timeseries"
  payload = [{
	"sensor_id":sensor,
	"samples": [
		{
		"time": time.time(),
		"value":Values
	}
	]
	}
	]
#  print url1
  payload = json.dumps(payload)
  response = requests.post(url1, headers = header, data = payload)
  try:
        response = response.json()
        return response
  except:
        atoken = getOauthToken()
        header = {"Authorization": "bearer " + atoken, 'content-type':'application/json'}
        response = requests.post(url1, headers = header, data=json.dumps(data), verify=False)
        return response.json()
 # print response
  return response.json()

def get_timeseries_data(URL, sensor):
  sensorUUID = sensor
  OauthToken = getOauthToken()
  header = {"Authorization": "bearer " + OauthToken, 'content-type':'application/json'}
  end_time = int(time.time())
  '''end_time=1460748294650
  start_time=22480252000
  print end_time'''
  start_time = int((datetime.now() - timedelta(days=30)).strftime("%s")) 
  url1 = URL+"api/sensor/%s/timeseries?start_time=%s&end_time=%s" % (sensorUUID, start_time,end_time)
  response = requests.get(url1, headers = header)
  return response.json()

def create_sensor(URL, vals, name, building, iden):
    url = URL
    url = url + "api/sensor"
   # print name
   # payload = {"data": {"Tags": ["Insitution:" + vals[0],"building:GHC", 'floor:'+vals[1], 'room:' + vals[2], +'ip:'+vals[3], 'networknumber:'+vals[4], 'address:'+vals[5], 'type:'+vals[6], 'objectID:'+vals[7]}}
    payload = {"data": {
	'name': name,
	'building': building,
	'identifier': iden}
	}
    #print payload
    OauthToken = getOauthToken()
    headers={'Authorization': 'Bearer '+OauthToken,'Content-Type':'application/json'}
    #headers={'Authorization': u'bearer '+OauthToken}
    iresponse = requests.post(url,headers=headers,data=json.dumps(payload),verify=False)
    print iresponse, URL, name, building, iden 
    return iresponse.json()
def add_tags(URL, name, tagname, tagvalue):
	url = URL
	url = url+"api/sensor/"+name['uuid']+"/tags"
	payload = {'data':[{
                'name': tagname,
                'value': tagvalue
            }]}
 	OauthToken = getOauthToken()
 	headers={'Authorization': 'Bearer '+OauthToken,'Content-Type':'application/json'}
        iresponse = requests.post(url,headers=headers,data=json.dumps(payload),verify=False)
  #	print iresponse
	return iresponse.json()




class Connector(object):
    """ Example Connector """

    def run(self, URL, Institution, Datafile, Building, LDPort, NetworkPort, JavaPort, SourceIP):
	#Create DataService SDK
	gateway = JavaGateway(gateway_parameters=GatewayParameters(port=int(JavaPort)))
#	gateway = JavaGateway()
	connector = gateway.entry_point.getConnector()
	global atoken
	global build
        build = Building
	atoken = getOauthToken()
        SensorIDs = list()	
	#Read in data from sensor file
	Sensorfile = Datafile
	sensors = open(Sensorfile,'r')
	i = 0
	IN= dict()
        val = 0
	oldip = ""
	for line in sensors:
		#Parse CSV Datafile. The current set up is for GHC buildings. The necessary elements are ip, objecttype, objectID, networknum, and address. The rest are used for naming
		partial = line.strip().split(',')
		null = 0
		for item in partial:
			null+=1
		floor = partial[1]
		space = partial[2]
		sensorName = partial[3]
		tag = partial[4]
		ip = partial[5]
		objecttype = partial[6]
		objectID = partial[7]
		networknum = partial[8]
		address = partial[9]
		port = NetworkPort
		#Data Filtering
		if(objecttype == '' or objectID == '' or address ==''):
			continue


		#Generate Sensors
		Tags = [Institution, floor, space, ip, networknum, address, objecttype, objectID]
		#Check if the sensor named below exists
		SensorName = str(Institution)+str(ip)+str(networknum)+str(address)+str(objecttype)+str(objectID) #Choose a naming convention that works for you. Names must be unique.
		Sensors = sensorlist(URL, Tags, SensorName)
		#If the sensor doesn't exist (only at installation), create it
		if len(Sensors['result']) < 1:
			#Create sensor if it doenst exist

			#Add building Tags to BD, if they don't aleady exist
			post_building_tag("Institution", str(Institution))
			post_building_tag("building", Building)
			post_building_tag("floor", str(floor))
			post_building_tag("room", str(space))
			post_building_tag("ip", str(ip))
			post_building_tag("networknumber", str(networknum))
			post_building_tag("address", str(address))
			post_building_tag("ObjectType", str(objecttype))
			post_building_tag("objectID", str(objectID))
			sensor_uuid = create_sensor(URL, Tags, SensorName, Building, 'TEST')
			add_tags(URL, sensor_uuid, "Institution", str(Institution))
			add_tags(URL, sensor_uuid, "building", Building)
			add_tags(URL, sensor_uuid, "floor", str(floor))
			add_tags(URL, sensor_uuid, "ip", str(ip))
			add_tags(URL, sensor_uuid, "room", str(space))
			add_tags(URL, sensor_uuid, "networknumber", str(networknum))
			add_tags(URL, sensor_uuid, "address", str(address))
			add_tags(URL, sensor_uuid, "ObjectType", str(objecttype))
			add_tags(URL, sensor_uuid, "objectID", str(objectID)) 
			
			Sensors = sensorlist(URL, Tags, SensorName)
		SensorIDs.append(Sensors['result'][0]['name']) 
		oldip = ip
		
			
		connector.addroom(Sensors['result'][0]['name'],str(ip),int(port), int(networknum), int(address), 0, int(objecttype), int(objectID), "bleep") #
    	time.sleep(60)
	while True:
		#Get Values from Java end of the connector
		values = connector.getCurrentValues(oldip, int(NetworkPort), int(LDPort), SourceIP)
		for value in values:
			#Write values to BD
		 	try:
				print value.getValue(), value.getRoom_id(), value.getObject_type(), value.getObject_id()
				resp = post_timeseries_data(URL, value.getRoom_id(), value.getValue())
			except:
					#this can happen if something goes wrong with the BD instance (network connectivity, excessive timeouts, etc.)
					print "fail"
		time.sleep(5)


if __name__ == '__main__':
    connector = Connector()
    #Replace arguments with BD URL and installation. 
    arguments = sys.argv
    URL = arguments[1]
    Institution = arguments[2]
    DataFile = arguments[3]
    Building = arguments[4]
    LDPort = arguments[5]
    NetworkPort = arguments[6]
    JavaPort = arguments[7]
    SourceIP = arguments[8]
    PermissionsFile = arguments[9]
    global client_id
    global client_secret
    global Ourl
    count = 0
    permise = open(PermissionsFile, 'r')
    for line in permise:
#	print line
	if(count ==0):
		client_id = line.strip()
		count +=1
	elif(count==1):
		client_secret = line.strip()
		count +=1
    Ourl = URL
 #   print URL, Institution, DataFile, Building
    connector.run(URL, Institution, Building, DataFile, LDPort, NetworkPort, JavaPort, SourceIP)
