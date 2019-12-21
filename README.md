# mqttmiot-airpurifier3
MIOT to MQTT for Xiaomi Mi Air Purifier 3

MIOT Spec: http://miot-spec.org/miot-spec-v2/instance?type=urn:miot-spec-v2:device:air-purifier:0000A007:zhimi-ma4:1

Requireds Python3

You need to setup this script by changing the following variables:
	miot_token="Your token"
	miot_did="My DID"
	miot_broker=<hostname/ip>

	mqtt_broker=<hostname/ip>
	mqtt_username=<username>
	mqtt_password=<password>
	mqtt_prefix="myprefix/"

You can get the token using various means (https://github.com/jghaanstra/com.xiaomi-miio/blob/master/docs/obtain_token.md)

DID can be discovered by issuing a "miIO.info" command.

It will periodically (with different intervals which depend on the data) update:
	- PM2.5 density
	- temperature
	- humidity
	- mode (AUTO, SLEEP, FAVORITE, NONE)
	- fanspeed (favorite mode)
	- light status
	- childlock status
	- power status
	- fault status

Everything is published on "state", ie: power/state .
Any command will be received on the item, ie: power .
The result of the command is published on "return", ie: power/return


