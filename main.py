import RPi.GPIO as GPIO
import time
import os
import atexit
import argparse


FAN_PIN = 19  # Default GPIO pin
PWM_FREQ = 25 # This is in kHz. The default is for the Noctua NF-A4x10. Look for the Target frequency in the spec of your fan. 

# Fan default settings
FAN_OFF = 0 
FAN_LOW = 30
FAN_HIGH = 70
FAN_MAX = 100

# Temperature thresholds
LOW_TEMP = 45
HIGH_TEMP = 60
MAX_TEMP = 70

OFFSET_THRESHOLD = 2 # Difference in temperature that will trigger a change in speed in Auto mode

WAIT_TIME = 1 #Sleep time between cycle


# Init the PWM fan
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(FAN_PIN, GPIO.OUT, initial=GPIO.LOW)
PWM_FAN = GPIO.PWM(FAN_PIN,PWM_FREQ)

# set the fan speed to 0.
def resetFan():
    PWM_FAN.start(FAN_OFF)

class PWMFan:
    def __init__(self, debug=None):
        self.debug = debug
        self.pwmfan = PWM_FAN
        self.last_value = 0

    def turn_off(self):
        self.pwmfan.start(FAN_OFF)
        return

    def set_value(self, speed):
        # Speed value must be 0.0 to 1.0
        
        self.pwmfan.start(speed) # round the speed value to 1 decimal
        if debug:
            print(f"fan speed set to {speed}%")
        return
        
    def get_value(self):
        return self.pwmfan.value

    def get_cpu_temp(self):
        res = os.popen('cat /sys/class/thermal/thermal_zone0/temp').readline()
        temp = float(res)/1000
        return temp

    def auto_fan_speed(self):
        temp = round(self.get_cpu_temp(), 1)
        offset = abs(temp - self.last_value)
        if debug:
            print(temp)
        if offset >= OFFSET_THRESHOLD:
            self.last_value = temp
            if temp < LOW_TEMP:
                self.set_value(FAN_OFF)
            if temp >= LOW_TEMP and temp < HIGH_TEMP:
                self.set_value(FAN_LOW)
            if temp >= HIGH_TEMP and temp < MAX_TEMP:
                self.set_value(FAN_HIGH)
            if temp >= MAX_TEMP:
                self.set_value(FAN_MAX)
        return


    def run(self):
        try:
            self.auto_fan_speed()
        except:
            resetFan()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Set debug to true")

    flags = parser.parse_args()
    debug = None
    try:
        if flags.debug:
            debug = True
        # Handle fan speed every WAIT_TIME sec
        fan = PWMFan(debug)

        while True:
            fan.run()
            time.sleep(1)
            
    except KeyboardInterrupt: # trap a CTRL+C keyboard interrupt
        resetFan()
    
    atexit.register(resetFan)