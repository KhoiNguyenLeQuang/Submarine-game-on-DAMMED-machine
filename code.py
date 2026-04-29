import board
import time
import math
import asyncio
import motorFunctions
import neoPixelFunctions as nf
import adafruit_icm20x
import adafruit_character_lcd.character_lcd_i2c as character_lcd
from submarine_engine import ArcadeGame

# Hardware Setup
i2c = board.I2C()
neoRing = nf.NeoPixelRing()
neoRing.brightness = 0.3
motor = motorFunctions.ECEGMotor(i2c)
motor.find_home()
imu = adafruit_icm20x.ICM20948(i2c, address=0x69)
lcd = character_lcd.Character_LCD_I2C(i2c, 16, 2)
lcd.backlight = True

game = ArcadeGame(lcd, neoRing)

# Global State
state = {
    "motor_angle": 0.0,
    "calibration_offset": 0.0,
    "max_turn_speed": 1.6,
    "min_tilt": 10.0
}

# Motor & Sensor Steering
async def steer_motor():
    while True:
        accel_x, accel_y, _ = imu.acceleration
        raw_tilt = math.degrees(math.atan2(accel_y, accel_x))
        tilt_angle = raw_tilt - state["calibration_offset"]

        if abs(tilt_angle) > state["min_tilt"]:
            tilt_angle = max(-90.0, min(90.0, tilt_angle))
            speed_multiplier = tilt_angle / 90.0
            
            # Update the angle
            state["motor_angle"] -= speed_multiplier * state["max_turn_speed"]
            state["motor_angle"] %= 360.0
            
            # Drive motor immediately
            motor.set_position_degrees(state["motor_angle"])
        
        # Yield for 10ms (100Hz motor refresh)
        await asyncio.sleep(0.01)

# Game Logic & Radar Tick
async def run_game_engine():
    game.update_lcd()
    while True:
        # This only runs every 0.5 seconds
        game.time_survived += 0.5
        game.update_lcd()
        
        # Engine math handles the LED radar
        game.process_tick(state["motor_angle"])
        
        await asyncio.sleep(0.5)

# Calibration & Launcher
async def main():
    # Perform Calibration before starting loops
    lcd.message = "Calibrating...\nKeep Still!"
    sum_tilt = 0.0
    for _ in range(50):
        ax, ay, _ = imu.acceleration
        sum_tilt += math.degrees(math.atan2(ay, ax))
        await asyncio.sleep(0.02)
    
    state["calibration_offset"] = sum_tilt / 50.0
    lcd.clear()
    
    # Launch both tasks simultaneously
    motor_task = asyncio.create_task(steer_motor())
    game_task = asyncio.create_task(run_game_engine())
    
    # Keep the script running
    await asyncio.gather(motor_task, game_task)

# Start the Async system
asyncio.run(main())
