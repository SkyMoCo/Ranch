
import time

from umqttsimple import MQTTClient
from machine import Pin, ADC
from time import sleep
import ubinascii
import machine
import micropython
import neopixel
import network
import esp
import math
from machine import Pin
esp.osdebug(None)
import gc
gc.collect()

pot = ADC(Pin(0))
pot.atten(ADC.ATTN_11DB)

np = neopixel.NeoPixel(machine.Pin(8), 1)

ssid = 'ForeverRanch'
password = 'KyleHotSpring'
mqtt_server = '192.168.1.21'
#EXAMPLE IP ADDRESS
#mqtt_server = '192.168.1.106'

client_id = ubinascii.hexlify(machine.unique_id())

topic_pub = b'ranch/pump/pressure'

last_message = 0
message_interval = 5

station = network.WLAN(network.STA_IF)

station.active(True)
station.connect(ssid, password)

while station.isconnected() == False:
  pass

print('Connection to network successful')


def connect_mqtt():
  global client_id, mqtt_server
  client = MQTTClient(client_id, mqtt_server)
  #client = MQTTClient(client_id, mqtt_server, user=your_username, password=your_password)
  client.connect()
  print('Connected to %s MQTT broker' % (mqtt_server))
  return client

def restart_and_reconnect():
  print('Failed to connect to MQTT broker. Reconnecting...')
  time.sleep(10)
  machine.reset()

def read_sensor():
  try:
    pot_value = pot.read()
    print(pot_value)
    return pot_value
  except OSError as e:
    return('Failed to read sensor.')

try:
  client = connect_mqtt()
except OSError as e:
  restart_and_reconnect()

while True:
  try:
    if (time.time() - last_message) > message_interval:
      pressure = read_sensor()
      print(pressure)
      led = math.floor((pressure * 600) /4096)
      np[0] = (0,led,
               0)
      np.write()
      msg = b'%d' % pressure
      client.publish(topic_pub, msg)
      last_message = time.time()
  except OSError as e:
    restart_and_reconnect()
