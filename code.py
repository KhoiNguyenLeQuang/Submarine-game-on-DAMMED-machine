import board
import time
import math
import motorFunctions
import neoPixelFunctions as nf
import adafruit_icm20x
import adafruit_character_lcd.character_lcd_i2c as character_lcd

# Import your custom standalone game engine library!
from submarine_engine import ArcadeGame

# Initialize Hardware
i2c = board.I2C()

neoRing = nf.NeoPixelRing()
neoRing.brightness = 0.3
neoRing.fill((0, 0, 0))

motor = motorFunctions.ECEGMotor(i2c)
motor.find_home()

imu = adafruit_icm20x.ICM20948(i2c, address=0x69)

lcd = character_lcd.Character_LCD_I2C(i2c, 16, 2)
lcd.backlight = True  

# Initialize Game Engine
game = ArcadeGame(lcd, neoRing)

# Motor Tracking Variables
current_motor_angle = 0.0   
MAX_TURN_SPEED = 1.6        ## Turn angle
MIN_TILT_ANGLE = 10.0       # 10-degree 

# Calibration Routine
def calibrate_imu():
    lcd.clear()
    lcd.message = "Calibrating...\nKeep Still!"
    time.sleep(2) 
    
    sum_tilt = 0.0
    for _ in range(50):
        ax, ay, az = imu.acceleration
        sum_tilt += math.degrees(math.atan2(ay, ax))
        time.sleep(0.02)
        
    lcd.clear()
    return sum_tilt / 50.0

calibration_offset = calibrate_imu()

# Main Game Loop
game.update_lcd()
last_tick_time = time.monotonic()

while True:
    
    # 1. READ SENSORS
    accel_x, accel_y, accel_z = imu.acceleration
    
    # 2. CALCULATE Y-AXIS TILT (Roll)
    raw_tilt = math.degrees(math.atan2(accel_y, accel_x))
    
    # Subtract the table's offset to get the TRUE tilt relative to the player
    tilt_angle = raw_tilt - calibration_offset
    
    # 3. APPLY DEADZONE (Ignore tilts less than 10 degrees)
    if abs(tilt_angle) > MIN_TILT_ANGLE:
        
        # 4. CAP AT 90 DEGREES MAXIMUM
        tilt_angle = max(-90.0, min(90.0, tilt_angle))
        
        # 5. CALCULATE PROPORTIONAL TURN SPEED
        speed_multiplier = tilt_angle / 90.0 
        turn_amount = speed_multiplier * MAX_TURN_SPEED
        
        # 6. UPDATE MOTOR ANGLE
        current_motor_angle -= turn_amount
        current_motor_angle %= 360.0
        
        motor.set_position_degrees(current_motor_angle)
        
    # 7. RUN GAME ENGINE TICK (Independent of the motor frame rate)
    current_time = time.monotonic()
    if current_time - last_tick_time >= 0.5: # 0.5 seconds keeps the radar objects moving smoothly
        game.time_survived += 0.5 
        game.update_lcd()
        
        # Tell the engine where the motor is pointing so it can calculate movement and collisions
        game.process_tick(current_motor_angle)
        
        last_tick_time = current_time
        
    time.sleep(0.00001)
