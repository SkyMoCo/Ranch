import uos
import usys
import machine
import time  # needed for ntptime and/or getting uptime
from time import sleep
import _thread
import re
import utime
import esp32
from machine import Pin, RTC, I2C
import network
import ntptime
import ubinascii
#import ssd1306
from umqttsimple import MQTTClient


import gc
gc.collect()

wifi_ssid = "ForeverRanch"
wifi_password = "KyleHotSprings"

counter = 0

#Wifi object
wlan = network.WLAN(network.STA_IF)


# MQTT Stuff
client_id = ubinascii.hexlify(machine.unique_id())
mqtt_server = '192.168.1.21'
publish_GPM = b'ranch/well/GPM'
publish_gallons = b'ranch/well/totalg'

def handle_interrupt(pin):
  global counter
  counter += 1

def print_machine_info():
    print("====================================")
    print(usys.implementation[0], uos.uname()[3],"\nrun on", uos.uname()[4])
    print("====================================")

def wifi_connect(fatal=True):
    global IP
    wlan.active(True)
    if not wlan.isconnected():
        print('\nConnecting to network', end='')
        wlan.connect(wifi_ssid, wifi_password)
        retry = 0
        while not wlan.isconnected():
            if retry >= 20:
                print('WiFi retry limited reached')
                if fatal:
                    restart_device()
                else:
                    return
            print('.', end='')
            utime.sleep(3.0)
            retry += 1
            pass
    print()
    print("Interface's MAC: ", ubinascii.hexlify(network.WLAN().config('mac'),':').decode()) # print the interface's MAC
    IP = wlan.ifconfig()
    print("Interface's IP/netmask/gw/DNS: ", IP,"\n") # print the interface's IP/netmask/gw/DNS addresses


# Resource for this
# https://embedded-things.blogspot.com/2021/10/esp32-c3micropython-ssd1306-i2c-oled.html
def setup_display():
    global oled_ssd1306
    oled_i2c = machine.I2C(0)
    
    print("Default I2C:", oled_i2c)
    try:
        oled_ssd1306 = ssd1306.SSD1306_I2C(128, 64, oled_i2c)
        print("Default SSD1306 I2C address:", oled_ssd1306.addr, "/", hex(oled_ssd1306.addr))
#        oled_ssd1306.text('Hello, World!', 0, 0, 1)
#        oled_ssd1306.show()
    except OSError as exc:
        print("OSError!", exc)
        if exc.errno == errno.ENODEV:
            print("No such device")
            print("~ bye ~")

# MQTT Functions
def connect_and_subscribe():
    global client_id, mqtt_server, topic_sub
#  client = MQTTClient(client_id, mqtt_server)
    client = MQTTClient(client_id, mqtt_server, port=1883, user=None, password=None, keepalive=65, ssl=False, ssl_params={})
    client.connect()
    print('Connected to %s MQTT broker' % (mqtt_server))
    return client

def restart_and_reconnect():
  print('Failed to connect to MQTT broker. Reconnecting...')
  time.sleep(10)
  machine.reset()


# Do some setup
ed = Pin(8, Pin.OUT)
pir = Pin(7, Pin.IN)

pir.irq(trigger=Pin.IRQ_FALLING, handler=handle_interrupt)
print_machine_info()
print("connect wifi")
wifi_connect()
#setup_display()

#oled_ssd1306.text('Water Flow Meter', 0, 0, 1)
#oled_ssd1306.text(str(IP),0,15,1)
#oled_ssd1306.show()

lastRead = time.ticks_ms()

totalGallons = 0
upTime = 0

try:
  client = connect_and_subscribe()
except OSError as e:
  restart_and_reconnect()

while True:
    # Count the pulses every 1000ms or so...
    elapsed = time.ticks_diff(time.ticks_ms(), lastRead)
    if ( elapsed > 60000):     # one minute
        upTime += 1

        pulsePerSec = counter
        counter = 0
        # One Inch flowmeter
        #totalGallons += pulsePerSec * .0008257 ;
        # 1 1/2 inch flowmeter
        totalGallons += pulsePerSec / 102.2;
        flowGPM = ((( 60000.0 / elapsed) * pulsePerSec) * 0.0264 * 60) / 27;
        #f'{totalGallons:.2f}'
        print('Uptime: ', upTime,' PulsePer: ', pulsePerSec, " Millisec: ", elapsed, "Gallons: ", f'{totalGallons:.2f}', "GPM ",  flowGPM )
        
#        oled_ssd1306.fill(0)
#        line1 = "Uptime: " + str(upTime)
#        line2 = "Current GPM " + str(counter)
#        line3 = "Total G: "+ str(totalGallons)
#        oled_ssd1306.text(line1,0,0,1)
#        oled_ssd1306.text(line2,0,25,1)
#        oled_ssd1306.text(line3,0,35,1)
#        oled_ssd1306.show()
        lastRead = time.ticks_ms();

        try:
            msg = b'#%.2f' % totalGallons
            client.publish(publish_gallons, msg)
            msg = b'#%.2f' % flowGPM
            client.publish(publish_GPM, msg)
        except OSError as e:
            restart_and_reconnect()

        sleep(1)
