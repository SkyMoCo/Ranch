import machine
import uos
import usys
from machine import Pin, RTC, I2C, SoftI2C
from machine import Pin
from time import sleep
import time
import neopixel

motion = False
counter = 0

def handle_interrupt(pin):
  global counter
  counter += 1
  global interrupt_pin
  interrupt_pin = pin 

led = Pin(8, Pin.OUT)
pir = Pin(7, Pin.IN)

pir.irq(trigger=Pin.IRQ_FALLING, handler=handle_interrupt)

lastRead = time.ticks_ms()
np = neopixel.NeoPixel(machine.Pin(8), 1)

np[0] = (0, 0, 0)
np.write()
time.sleep(1)
np[0] = (100, 100, 20)
np.write()

for i in range(256):
    np[0] = (255-i, 255-i, 255-i)
    np.write()
    time.sleep_ms(10)

while True:
    # Count the pulses every 1000ms or so...
    elapsed = time.ticks_diff(time.ticks_ms(), lastRead)
    if ( elapsed > 999):
        pulsepersec = counter
        print('Counter is ', counter, " Elapsed is ", elapsed )
        lastRead = time.ticks_ms();
    sleep(1)

