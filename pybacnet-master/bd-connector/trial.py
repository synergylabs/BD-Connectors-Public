import bacnet

bacnet.Init(None, None)
print bacnet.whois_hack()
devices = bacnet.whois(10)
index = 0
for dev in devices:
	print str(index) + '\t' + str(dev['device_id'])
	index += 1 
	
my_dev = devices[7]
print bacnet.read_prop(my_dev, bacnet.OBJECT_DEVICE, my_dev['device_id'], bacnet.PROP_OBJECT_LIST, 0)
