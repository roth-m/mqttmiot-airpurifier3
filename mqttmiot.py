import sys
import time
import socket
import json
from multiprocessing import Queue
import paho.mqtt.client as paho
import miio

# Constants
mqtt_username="YOUR USERNAME"
mqtt_password="YOUR PASSWORD"
mqtt_prefix="MQTTPREFIX"
mqtt_broker="MQTTBROKERIP"
miot_broker="MIOT-AIRPURIFIER-IP"
miot_port=54321
miot_len_max=1480
miot_did=u"MY DID";
miot_token="MY TOKEN";

q = Queue(maxsize=100)

def dumpclean(obj):
	if type(obj) == dict:
		print("It is a DICT")
		for k, v in obj.items():
			if hasattr(v, '__iter__'):
				print(k)
				dumpclean(v)
			else:
				print('%s : %s' % (k, v))
	elif type(obj) == list:
		for v in obj:
			if hasattr(v, '__iter__'):
				dumpclean(v)
			else:
				print(v)
	else:
		print(obj)



#define callback
def on_message(client, userdata, message):
	global q

	print("received message =",str(message.payload.decode("utf-8"))," on: ",message.topic)
	item=message.topic[len(mqtt_prefix):]
	print("Item: "+item)
	command=str(message.payload.decode("utf-8"))
	if item == "power":
		if command.upper() == "ON":
			q.put([ "power","set_properties", [{"did":miot_did,"siid":2,"piid":2,"value": True}]])
		else:
			q.put([ "power","set_properties", [{"did": miot_did,"siid":2,"piid":2,"value": False}]])
		q.put([ "power","get_properties", [{"did":miot_did,"siid":2,"piid":2}]])

	if item == "fanspeed":
		valper=int(float(command.upper()))
		if valper > 0:
			miotvalue=int(300//(100/valper))*10
		else:
			miotvalue=0
		q.put([ "mode","set_properties", [{"did":miot_did,"siid":2,"piid":5,"value":2}]])
		q.put([ "fanspeed","set_properties", [{"did":miot_did,"siid":10,"piid":8,"value": miotvalue}]])
		q.put([ "mode","get_properties", [{"did":miot_did,"siid":2,"piid":5}]])
		q.put([ "fanspeed","get_properties", [{"did":miot_did,"siid":10,"piid":8}]])
	
	if item == "mode":
		if command.upper() == "AUTO":
			q.put([ "mode","set_properties", [{"did":miot_did,"siid":2,"piid":5,"value":0}]])
		if command.upper() == "SLEEP":
			q.put([ "mode","set_properties", [{"did":miot_did,"siid":2,"piid":5,"value":1}]])
		if command.upper() == "FAVORITE":
			q.put([ "mode","set_properties", [{"did":miot_did,"siid":2,"piid":5,"value":2}]])
		if command.upper() == "NONE":
			q.put([ "mode","set_properties", [{"did":miot_did,"siid":2,"piid":5,"value":3}]])
		q.put([ "mode","get_properties", [{"did":miot_did,"siid":2,"piid":5}]])
		
	if item == "light":
		if command.upper() == "ON":
			q.put([ "light","set_properties", [{"did":miot_did,"siid":6,"piid":1,"value":0}]])
		if command.upper() == "SOFT":
			q.put([ "light","set_properties", [{"did":miot_did,"siid":6,"piid":1,"value":1}]])
		if command.upper() == "OFF":
			q.put([ "light","set_properties", [{"did":miot_did,"siid":6,"piid":1,"value":2}]])
		q.put([ "light","get_properties", [{"did":miot_did,"siid":6,"piid":1}]])
		
	if item == "childlock":
		if command.upper() == "ON":
			q.put([ "childlock","set_properties", [{"did":miot_did,"siid":7,"piid":1,"value": True}]])
		else:
			q.put([ "childlock","set_properties", [{"did": miot_did,"siid":7,"piid":1,"value": False}]])
		q.put([ "childlock","get_properties", [{"did":miot_did,"siid":7,"piid":1}]])
		

client= paho.Client("mqttmiot-001") #create client object client1.on_publish = on_publish #assign function to callback client1.connect(broker,port) #establish connection client1.publish("house/bulb1","on")
client.username_pw_set(mqtt_username, mqtt_password)
######Bind function to callback
client.on_message=on_message
#####
print("connecting to broker ",mqtt_broker)
client.connect(mqtt_broker)#connect
client.loop_start() #start loop to process received messages
client.subscribe(mqtt_prefix+"power")#subscribe
client.subscribe(mqtt_prefix+"mode")#subscribe
client.subscribe(mqtt_prefix+"fanspeed")#subscribe
client.subscribe(mqtt_prefix+"light")#subscribe
client.subscribe(mqtt_prefix+"childlock")#subscribe

count_idle_messages=0
count_interval_messages=0

# 6 seconds between set and get commands (time for value to be updated)
interval_messages=60

miot_retry=0

ap=miio.Device(ip=miot_broker, token=miot_token, lazy_discover=True)
# miio old ap.do_discover()
ap.send_handshake()

while True:
	while not q.empty() and count_interval_messages==0:
		print("Something in the queue")
		# req : topic , miio_msg
		req=q.get();
		print("Sending: "+str(req[1])+ " - "+str(req[2]))
		miot_retry=3
		while miot_retry>0:
			try:
				ap._discovered = True
				ret=ap.raw_command(req[1], req[2]);
				#dumpclean(ret)
				ret=ret[0]
				if req[1]=="get_properties":
					val=ret["value"]
					if req[0]=="fanspeed":
						val=(val*100)//3000;
					if req[0]=="temperature":
						val="{:.2f}".format(float(val));
					if req[0]=="mode":
						if val==0:
							val="AUTO"
						if val==1:
							val="SLEEP"
						if val==2:
							val="FAVORITE"
						if val==3:
							val="NONE"
					if req[0]=="light":
						if val==0:
							val="ON"
						if val==1:
							val="SOFT"
						if val==2:
							val="OFF"
					if req[0]=="fault":
						if val==0:
							val="NONE"
						if val==1:
							val="RUN"
						if val==2:
							val="STUCK"
						if val==3:
							val="NOSENSOR"
						if val==4:
							val="ERRORHUM"
						if val==5:
							val="ERRORTEMP"
					if req[0]=="power" or req[0]=="childlock":
						if val==1 or val==True or val=="True" or val=="true" or val=="TRUE":
							val="ON"
						else:
							val="OFF"
					client.publish(mqtt_prefix+req[0]+"/state",val)
					print("Publishing: "+mqtt_prefix+req[0]+"/state",val)
				if req[1]=="set_properties":
					client.publish(mqtt_prefix+req[0]+"/result",ret["code"])
					print("Publishing: "+mqtt_prefix+req[0]+"/result",ret["code"])
					count_interval_messages=interval_messages
				miot_retry=0
			except Exception as e:
				print("No valid reply! Bad request?")
				miot_retry=miot_retry-1
				time.sleep(0.500)
#	print("Waiting...")
	time.sleep(0.100);
	count_idle_messages=count_idle_messages+1;
	if count_interval_messages>0:
		count_interval_messages=count_interval_messages-1
	if count_idle_messages>0:
			# Every hour
			if (count_idle_messages%36700)==0:
				q.put([ "filter","get_properties", [{"did":miot_did,"siid":4,"piid":3}]])
			# Every minute + 19s
			if (count_idle_messages%790)==0:
				q.put([ "fault","get_properties", [{"did":miot_did,"siid":2,"piid":1}]])
			if (count_idle_messages%850)==0:
				q.put([ "power","get_properties", [{"did":miot_did,"siid":2,"piid":2}]])
			if (count_idle_messages%630)==0:
				q.put([ "fanspeed","get_properties", [{"did":miot_did,"siid":10,"piid":8}]])
			if (count_idle_messages%690)==0:
				q.put([ "mode","get_properties", [{"did":miot_did,"siid":2,"piid":5}]])
			if (count_idle_messages%960)==0:
				q.put([ "light","get_properties", [{"did":miot_did,"siid":6,"piid":1}]])
			# Every 5 minutes
			if (count_idle_messages%3100)==0:
				q.put([ "temperature","get_properties", [{"did":miot_did,"siid":3,"piid":8}]])
			if (count_idle_messages%3200)==0:
				q.put([ "humidity","get_properties", [{"did":miot_did,"siid":3,"piid":7}]])
			if (count_idle_messages%3300)==0:
				q.put([ "pm25","get_properties", [{"did":miot_did,"siid":3,"piid":6}]])
			if count_idle_messages>864000:
				count_idle_messages=0
		
		
client.disconnect() #disconnect
client.loop_stop() #stop loop

