"""
PINS IN USE
>NeoPixel -> board.D5
>Motor -> board.I2C
>Hall sensor -> board.D16 (A2)
>IMU (ICM20948) -> board.I2C (STEMMA QT, 0x69)
>Character LCD -> board.I2C (STEMMA QT, 0x20)

ECEG 201: Submarine Game Controller (Auto-Calibrating Velocity Steering)
"""

import board
import time
import math
import supervisor
import motorFunctions
import neoPixelFunctions as nf

import adafruit_icm20x
import adafruit_character_lcd.character_lcd_i2c as character_lcd

# Initialize I2C Bus
i2c = board.I2C()

# Initialize Hardware

NEO_BRIGHTNESS = 0.3
neoRing = nf.NeoPixelRing()
neoRing.brightness = NEO_BRIGHTNESS
neoRing.fill((0, 0, 0))

motor = motorFunctions.ECEGMotor(i2c)
motor.find_home()

imu = adafruit_icm20x.ICM20948(i2c, address=0x69)

lcd_columns = 16
lcd_rows = 2
lcd = character_lcd.Character_LCD_I2C(i2c, lcd_columns, lcd_rows)
lcd.backlight = True  

# Game Variables
coins_collected = 0
time_survived = 0

# Motor Tracking Variables
current_motor_angle = 0.0   
MAX_TURN_SPEED = 8.0        

# Helper Functions 

def UpdateLCD():
    display_text = f"Time: {time_survived}s      \nCoins: {coins_collected}      "
    lcd.message = display_text

def HandleGameEvent(command):
    global coins_collected, time_survived
    try:
        if command == "COIN":
            coins_collected += 1
            UpdateLCD()
            neoRing.fill((255, 255, 0)) 
            
        elif command.startswith("ICEBERG:"):
            distance = int(command.split(":")[1])
            blue_intensity = int(255 - (distance * 2.35))
            blue_intensity = max(0, min(255, blue_intensity))
            neoRing.fill((0, 0, blue_intensity))
            
        elif command.startswith("TIME:"):
            time_survived = int(command.split(":")[1])
            UpdateLCD()
    except Exception as e:
        pass 

# Calibration Routine 

lcd.clear()
lcd.message = "Calibrating...\nKeep Still!"
print("Calibrating... please leave the controller flat on the table.")

# Give the user 2 seconds to let go of the controller
time.sleep(2) 

sum_tilt = 0.0
samples = 50

# Take 50 rapid readings of the table's natural tilt
for _ in range(samples):
    ax, ay, az = imu.acceleration
    sum_tilt += math.degrees(math.atan2(ay, ax))
    time.sleep(0.02)

# Average them out to find the table's "Zero" point
calibration_offset = sum_tilt / samples

print(f"Calibration Complete! Table offset is: {calibration_offset:.2f} degrees.")
lcd.clear()

# Main Game Loop 

UpdateLCD()
print("Submarine Steering Ready!")

while True:
    # 1. READ SENSORS
    accel_x, accel_y, accel_z = imu.acceleration
    
    # Send raw data to the PC game 
    print(f"{accel_x:.2f},{accel_y:.2f},{accel_z:.2f}")
    
    # 2. CALCULATE Y-AXIS TILT (Roll)
    raw_tilt = math.degrees(math.atan2(accel_y, accel_x))
    
    # Subtract the table's offset to get the TRUE tilt relative to the player
    tilt_angle = raw_tilt - calibration_offset
    
    # 3. APPLY DEADZONE (Ignore tilts less than 5 degrees)
    if abs(tilt_angle) > 5.0:
        
        # 4. CAP AT 90 DEGREES MAXIMUM
        tilt_angle = max(-90.0, min(90.0, tilt_angle))
        
        # 5. CALCULATE PROPORTIONAL TURN SPEED
        speed_multiplier = tilt_angle / 90.0 
        turn_amount = speed_multiplier * MAX_TURN_SPEED
        
        # 6. UPDATE MOTOR ANGLE
        current_motor_angle -= turn_amount
        current_motor_angle %= 360.0
        
        motor.set_position_degrees(current_motor_angle)
        
    # 4. RECEIVE DATA FROM GAME
    if supervisor.runtime.serial_bytes_available:
        incoming_data = input().strip()
        HandleGameEvent(incoming_data)
    
    time.sleep(0.05)
