import time
import random
import math

class ArcadeGame:
    def __init__(self, lcd, neo_ring):
        self.lcd = lcd
        self.neo_ring = neo_ring
        self.coins_collected = 0
        self.time_survived = 0
        self.game_objects = []
        
        # FIX FOR HARDWARE MISALIGNMENT:
        # If the motor is pointing at a coin, but the LED is physically out of place,
        # change this number (e.g., 90, 180, -90) to rotate the digital lights.
        self.LED_OFFSET = 0 

    def update_lcd(self):
        display_text = f"Time: {int(self.time_survived)}s      \nCoins: {self.coins_collected}      "
        self.lcd.message = display_text

    def trigger_game_over(self):
        self.neo_ring.fill((255, 0, 0))
        self.lcd.clear()
        self.lcd.message = "CRASHED!\nGame Over..."
        time.sleep(3.0)
        
        self.coins_collected = 0
        self.time_survived = 0
        self.game_objects = []
        self.lcd.clear()
        self.update_lcd()

    def draw_radar(self):
        self.neo_ring.fill((0, 0, 0))
        for obj in self.game_objects:
            # Calculate distance using X and Y coordinates
            dist = math.sqrt(obj['x']**2 + obj['y']**2)
            
            if dist > 4.5: continue # Invisible if too far away
            
            # Calculate angle and apply the hardware alignment offset
            angle = math.degrees(math.atan2(obj['y'], obj['x'])) % 360
            led_index = int(((angle + self.LED_OFFSET) / 360.0) * 24) % 24
            
            r, g, b = 0, 0, 0
            if obj['type'] == 'COIN':
                if dist > 2.5:   r, g, b = 15, 15, 0      # Far
                elif dist > 1.0: r, g, b = 60, 60, 0      # Medium
                else:            r, g, b = 255, 255, 0    # Close
            elif obj['type'] == 'ICEBERG':
                if dist > 2.5:   r, g, b = 0, 0, 15
                elif dist > 1.0: r, g, b = 0, 0, 60
                else:            r, g, b = 0, 0, 255
                
            self.neo_ring.set_index(led_index, (r, g, b))

    def process_tick(self, current_motor_angle):
        # 1. THE SUBMARINE DRIVES FORWARD
        # We calculate how far the submarine moves in the X and Y direction
        move_speed = 0.5 
        dx = math.cos(math.radians(current_motor_angle)) * move_speed
        dy = math.sin(math.radians(current_motor_angle)) * move_speed
        
        surviving_objects = []
        
        for obj in self.game_objects:
            # 2. SHIFT THE WORLD AROUND THE SUBMARINE
            obj['x'] -= dx
            obj['y'] -= dy
            
            dist = math.sqrt(obj['x']**2 + obj['y']**2)
            
            # 3. REALISTIC COLLISIONS
            if dist <= 0.5: # You drove directly over it!
                if obj['type'] == 'COIN':
                    self.coins_collected += 1
                    self.update_lcd()
                    self.neo_ring.fill((0, 255, 0))
                    time.sleep(0.1)
                elif obj['type'] == 'ICEBERG':
                    self.trigger_game_over()
                    return
            elif dist > 6.0:
                pass # It faded away behind you, despawn it to save memory
            else:
                surviving_objects.append(obj)
                
        self.game_objects = surviving_objects
        
        # 4. SPAWN NEW OBJECTS AHEAD OF THE SUBMARINE
        if random.random() < 0.8: 
            new_type = 'COIN' if random.random() < 0.4 else 'ICEBERG'
            
            # Spawn them in a cone slightly in front of where you are steering
            spawn_angle = current_motor_angle + random.uniform(-60, 60)
            spawn_dist = 4.5 
            
            new_x = math.cos(math.radians(spawn_angle)) * spawn_dist
            new_y = math.sin(math.radians(spawn_angle)) * spawn_dist
            
            self.game_objects.append({'type': new_type, 'x': new_x, 'y': new_y})
            
        self.draw_radar()
