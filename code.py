"""
PINS IN USE
>NeoPixel -> board.D5
>Motor -> board.I2C
>Hall sensor -> board.D16 (A2)
>IMU (ICM20948) -> board.I2C (STEMMA QT, 0x69)
>Character LCD -> board.I2C (STEMMA QT, 0x20)

ECEG 201: Standalone Submarine Arcade Game
"""

import board
import time
import math
import random  # Added for spawning game objects
import motorFunctions
import neoPixelFunctions as nf

import adafruit_icm20x
import adafruit_character_lcd.character_lcd_i2c as character_lcd

# Initialize I2C Bus
i2c = board.I2C()

# --- Initialize Hardware ---

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

# --- Game Engine Variables ---
coins_collected = 0
time_survived = 0
game_objects = []  # Holds active coins and icebergs

# --- Motor Tracking Variables ---
current_motor_angle = 0.0   
MAX_TURN_SPEED = 8.0        
MIN_TILT_ANGLE = 10.0       

################################################################# 
# Game Logic Functions ##########################################
#################################################################

def UpdateLCD():
    display_text = f"Time: {time_survived}s      \nCoins: {coins_collected}      "
    lcd.message = display_text

def TriggerGameOver():
    global coins_collected, time_survived, game_objects
    
    # Red screen of death
    neoRing.fill((255, 0, 0))
    lcd.clear()
    lcd.message = "CRASHED!\nGame Over..."
    time.sleep(3.0)
    
    # Reset Game State
    coins_collected = 0
    time_survived = 0
    game_objects = []
    lcd.clear()
    UpdateLCD()

def DrawRadar():
    """Maps all active game objects to the 24 LEDs on the NeoPixel ring based on angle and distance"""
    neoRing.fill((0, 0, 0))
    
    for obj in game_objects:
        # Convert the object's 0-359 angle into one of the 24 LEDs on the ring
        led_index = int((obj['angle'] / 360.0) * 24) % 24
        
        dist = obj['distance']
        r, g, b = 0, 0, 0
        
        if obj['type'] == 'COIN':
            if dist == 3:   r, g, b = 15, 15, 0      # Far: Dim Yellow
            elif dist == 2: r, g, b = 60, 60, 0      # Med: Medium Yellow
            elif dist == 1: r, g, b = 255, 255, 0    # Close: Bright Yellow
                
        elif obj['type'] == 'ICEBERG':
            if dist == 3:   r, g, b = 0, 0, 15       # Far: Dim Blue
            elif dist == 2: r, g, b = 0, 0, 60       # Med: Medium Blue
            elif dist == 1: r, g, b = 0, 0, 255      # Close: Bright Blue
            
        neoRing.set_index(led_index, (r, g, b))

def ProcessGameTick():
    """Runs once per second to move objects, check collisions, and spawn new ones."""
    global coins_collected, game_objects
    
    surviving_objects = []
    
    # 1. Move everything closer
    for obj in game_objects:
        obj['distance'] -= 1
        
        # 2. Check collisions for objects that reached the submarine (Distance 0)
        if obj['distance'] <= 0:
            
            # Calculate how far off the player's steering is from the object
            angle_diff = abs((current_motor_angle - obj['angle'] + 180) % 360 - 180)
            
            # If the motor is pointing within 15 degrees of the object, it's a hit!
            if angle_diff <= 15.0: 
                if obj['type'] == 'COIN':
                    coins_collected += 1
                    UpdateLCD()
                    neoRing.fill((0, 255, 0)) # Flash green for success
                    time.sleep(0.1)
                elif obj['type'] == 'ICEBERG':
                    TriggerGameOver()
                    return # Stop processing, the game is over!
            else:
                # If they didn't hit the iceberg, they dodged it successfully!
                pass 
        else:
            # Object is still far away, keep it on the radar
            surviving_objects.append(obj)
            
    game_objects = surviving_objects
    
    # 3. Randomly spawn new objects at the edge of the radar (Distance 3)
    if random.random() < 0.7: # 70% chance to spawn something every second
        # 40% chance it's a coin, 60% chance it's an iceberg
        new_type = 'COIN' if random.random() < 0.4 else 'ICEBERG'
        new_angle = random.uniform(0, 359)
        game_objects.append({'type': new_type, 'angle': new_angle, 'distance': 3})
        
    DrawRadar()

################################################################# 
# Calibration ###################################################
#################################################################

lcd.clear()
lcd.message = "Calibrating...\nKeep Still!"

time.sleep(2) 

sum_tilt = 0.0
samples = 50

for _ in range(samples):
    ax, ay, az = imu.acceleration
    sum_tilt += math.degrees(math.atan2(ay, ax))
    time.sleep(0.02)

calibration_offset = sum_tilt / samples
lcd.clear()

################################################################# 
# Main Game Loop ################################################
#################################################################

UpdateLCD()
print("Game Booted! Disconnect from PC whenever ready.")

# Timer for the game engine
last_tick_time = time.monotonic()
TICK_RATE = 1.0 # The game progresses every 1.0 seconds

while True:
    
    # --- 1. SENSOR STEERING (Runs constantly) ---
    accel_x, accel_y, accel_z = imu.acceleration
    raw_tilt = math.degrees(math.atan2(accel_y, accel_x))
    tilt_angle = raw_tilt - calibration_offset
    
    if abs(tilt_angle) > MIN_TILT_ANGLE:
        tilt_angle = max(-90.0, min(90.0, tilt_angle))
        speed_multiplier = tilt_angle / 90.0 
        turn_amount = speed_multiplier * MAX_TURN_SPEED
        
        current_motor_angle -= turn_amount
        current_motor_angle %= 360.0
        motor.set_position_degrees(current_motor_angle)
        
    # --- 2. GAME ENGINE TICK (Runs once per second) ---
    # We use time.monotonic() to run the game independently of the fast steering loop
    current_time = time.monotonic()
    if current_time - last_tick_time >= TICK_RATE:
        time_survived += 1
        UpdateLCD()
        ProcessGameTick()
        last_tick_time = current_time
        
    time.sleep(0.05)
