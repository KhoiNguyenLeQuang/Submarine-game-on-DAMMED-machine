"""
PINS IN USE
>NeoPixel -> board.D5
>Motor -> board.I2C
>Hall sensor -> board.D16 (A2)
>IMU (ICM20x) -> board.I2C (STEMMA QT)
>Character LCD -> board.I2C (STEMMA QT)

ECEG 201: Submarine Game Controller
"""

import board
import time
import math
import supervisor
import motorFunctions
import neoPixelFunctions as nf

# New Sensor Libraries 
import adafruit_icm20x
import adafruit_character_lcd.character_lcd_i2c as character_lcd

# Initialize I2C Bus
i2c = board.I2C()

# Initialize Hardware

# 1. NeoPixels
NEO_BRIGHTNESS = 0.3
neoRing = nf.NeoPixelRing()
neoRing.brightness = NEO_BRIGHTNESS
neoRing.fill((0, 0, 0))

# 2. Stepper Motor (Compass Arrow)
motor = motorFunctions.ECEGMotor(i2c)
motor.find_home()

# 3. IMU (Gyro/Accelerometer)
imu = adafruit_icm20x.ICM20649(i2c, address=0x69)

# 4. Character LCD
lcd_columns = 16
lcd_rows = 2
lcd = character_lcd.Character_LCD_I2C(i2c, lcd_columns, lcd_rows)
lcd.backlight = True
lcd.clear()
lcd.message = "Submarine OS\nBooting up..."
time.sleep(2) # Show boot message for 2 seconds

# --- Game Variables ---
coins_collected = 0
time_survived = 0

# Helper Functions 
def UpdateLCD():
    """
    Updates the character LCD. We use spaces at the end of the 
    strings to overwrite any leftover characters from previous numbers.
    """
    # \n moves the text to the second row
    display_text = f"Time: {time_survived}s      \nCoins: {coins_collected}      "
    lcd.message = display_text

def CalculateDirection(accel_x, accel_y):
    """
    Reads the tilt of the controller and calculates the angle 
    to point the motor arm (0 to 360 degrees).
    """
    # math.atan2 returns angle in radians from -pi to pi
    angle_rad = math.atan2(accel_y, accel_x)
    angle_deg = math.degrees(angle_rad)
    
    # Normalize to 0-360 degrees for the motor
    if angle_deg < 0:
        angle_deg += 360
        
    return angle_deg

def HandleGameEvent(command):
    """
    Parses serial data sent FROM the PC game TO the controller.
    Expected formats: "COIN", "ICEBERG:distance", "TIME:seconds"
    """
    global coins_collected, time_survived
    
    try:
        if command == "COIN":
            coins_collected += 1
            UpdateLCD()
            # Flash NeoPixels Yellow for a coin
            neoRing.fill((255, 255, 0)) 
            
        elif command.startswith("ICEBERG:"):
            # Distance from 0 (crash) to 100 (far away)
            distance = int(command.split(":")[1])
            
            # Map distance to blue intensity (closer = darker/brighter blue)
            blue_intensity = int(255 - (distance * 2.35))
            blue_intensity = max(0, min(255, blue_intensity))
            neoRing.fill((0, 0, blue_intensity))
            
        elif command.startswith("TIME:"):
            time_survived = int(command.split(":")[1])
            UpdateLCD()
            
    except Exception as e:
        pass # Ignore malformed serial data to prevent crashes


# Main Game Loop 
UpdateLCD()
print("Submarine Controller Ready!")

while True:
    # 1. READ SENSORS (Player Input)
    accel_x, accel_y, accel_z = imu.acceleration
    
    # 2. SEND DATA TO GAME 
    # Print as a clean CSV string so the PC game can parse it easily
    print(f"{accel_x:.2f},{accel_y:.2f},{accel_z:.2f}")
    
    # 3. UPDATE MOTOR (Compass pointing direction of travel)
    heading_angle = CalculateDirection(accel_x, accel_y)
    motor.set_position_degrees(heading_angle)
    
    # 4. RECEIVE DATA FROM GAME (Environmental Alerts)
    if supervisor.runtime.serial_bytes_available:
        incoming_data = input().strip()
        HandleGameEvent(incoming_data)
    
    # Game loop delay (approx 20 updates per second)
    time.sleep(0.05)
