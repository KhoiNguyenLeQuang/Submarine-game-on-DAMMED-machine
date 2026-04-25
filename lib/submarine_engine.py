import time
import random

class ArcadeGame:
    def __init__(self, lcd, neo_ring):
        # The engine takes control of the screen and lights
        self.lcd = lcd
        self.neo_ring = neo_ring
        
        # Internal Game Variables
        self.coins_collected = 0
        self.time_survived = 0
        self.game_objects = []

    def update_lcd(self):
        display_text = f"Time: {self.time_survived}s      \nCoins: {self.coins_collected}      "
        self.lcd.message = display_text

    def trigger_game_over(self):
        self.neo_ring.fill((255, 0, 0))
        self.lcd.clear()
        self.lcd.message = "CRASHED!\nGame Over..."
        time.sleep(3.0)
        
        # Reset the game
        self.coins_collected = 0
        self.time_survived = 0
        self.game_objects = []
        self.lcd.clear()
        self.update_lcd()

    def draw_radar(self):
        self.neo_ring.fill((0, 0, 0))
        for obj in self.game_objects:
            led_index = int((obj['angle'] / 360.0) * 24) % 24
            dist = obj['distance']
            r, g, b = 0, 0, 0
            
            if obj['type'] == 'COIN':
                if dist == 3:   r, g, b = 15, 15, 0
                elif dist == 2: r, g, b = 60, 60, 0
                elif dist == 1: r, g, b = 255, 255, 0
            elif obj['type'] == 'ICEBERG':
                if dist == 3:   r, g, b = 0, 0, 15
                elif dist == 2: r, g, b = 0, 0, 60
                elif dist == 1: r, g, b = 0, 0, 255
                
            self.neo_ring.set_index(led_index, (r, g, b))

    def process_tick(self, current_motor_angle):
        surviving_objects = []
        
        for obj in self.game_objects:
            obj['distance'] -= 1
            
            if obj['distance'] <= 0:
                angle_diff = abs((current_motor_angle - obj['angle'] + 180) % 360 - 180)
                
                # Collision detected!
                if angle_diff <= 15.0: 
                    if obj['type'] == 'COIN':
                        self.coins_collected += 1
                        self.update_lcd()
                        self.neo_ring.fill((0, 255, 0))
                        time.sleep(0.1)
                    elif obj['type'] == 'ICEBERG':
                        self.trigger_game_over()
                        return # Stop processing, game over
            else:
                surviving_objects.append(obj)
                
        self.game_objects = surviving_objects
        
        # Randomly spawn new items
        if random.random() < 0.7: 
            new_type = 'COIN' if random.random() < 0.4 else 'ICEBERG'
            new_angle = random.uniform(0, 359)
            self.game_objects.append({'type': new_type, 'angle': new_angle, 'distance': 3})
            
        self.draw_radar()