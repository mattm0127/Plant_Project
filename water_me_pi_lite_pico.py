import sys
import os
import time
#import board
import datetime
import textwrap as tw
import requests

import pygame
#from adafruit_seesaw.seesaw import Seesaw
import random as r

class SensorClient:
    """Class for getting data from the sensor."""
    base_url = 'http://'
        
    def __init__(self, pico_w_ip:str):
        self.pico_w_ip = pico_w_ip
        self.pico_w_port = 'Your Pico W Port:int'
            
    def _make_sensor_request(self, sensor_data_request):
        url = f"{self.base_url}{self.pico_w_ip}:{self.pico_w_port}/{sensor_data_request}"
        try:
            response = requests.get(url, timeout=1)
            value = response.text
            return value
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")

    def get_values(self):
        combined_values = self._make_sensor_request('moisture-temperature')
        return combined_values.split(',')
    
    def get_moisture_value(self):
        moisture_value = self._make_sensor_request('moisture')
        return moisture_value

    def get_temperature_value(self):
        temperature_value = self._make_sensor_request('temperature')
        return temperature_value


class WaterMeLite:
    """The main class for the WaterMeLite project."""

    def __init__(self):
        """Initiate the main variables for the class object."""
        # Create the sensor data.
        self.sensor_client = SensorClient('Your Pico W IP')
        self.timeout_timer = 0

        # Initiate pygame display.
        pygame.init()
        pygame.mouse.set_visible(False)
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((720, 480), pygame.NOFRAME)
        self.screen_rect = self.screen.get_rect()
        self.bg = pygame.image.load('images/bg_2.jpg')
        self.secret_bg = pygame.image.load('images/magic_horse.jpg')

        # Global Lists and strings.
        self.moisture_value = 0
        self.temperature_value = 0
        self.last_watered_list = [] 
        self.last_water_str = "Waiting for Water..."

        # Database for responses to system condition.
        self.phrases = {
                        # Plant lines
                        0: ["I'm nice and moist.", 
                            "I'm all filled up for now.",
                            "I'm cleaning the air for you...you're welcome.",
                            "Take care of me and there is a chance I bloom.",
                            "If one group has 6 leaves, you're lucky.",
                            "If one group has 7 leaves, you're even luckier.",
                            "I filter Xylene, Benzene and more from the air.",
                            "My 5 Leaves: Metal, Wind, Fire, Water and Earth."], 
                        # Neutral facts
                        1: ["Banana is actually an Arabic word for fingers.",
                            "Oak trees start producing acorns at 50 years old.", 
                            "Apples, onions and potatoes have the same taste.",
                            "Around 70,000 plants are used in medicine.",
                            "Dandelions can be eaten whole, all of it.",
                            "Chemicals from cut grass can relieve stress.",
                            "85% of all plantlife is found in the ocean.",
                            "Plants communicate through roots with chemicals.",], 
                        # Dry lines
                        2: ["I haven't been filled up in awhile.",
                            "Please make me wet.",
                            "Are you trying to kill me?",],
                        }

        # Global Timers and randoms for various changes.
        self.blink_timer = 0
        self.rand_blink_len = r.randint(9, 16) # Determine the length of time or the norm befer the 'different' ie open vs 'blinking'
        self.pupil_timer = 0
        self.rand_pup_len = r.randrange(15, 25) # Same as above
        self.rand_pup_loc = r.randrange(0,3) # Determines the random location pupil is looking
        self.phrase_timer = 0
        self.rand_phrase_len = r.randrange(6, 11)
        self.rand_key = r.randrange(0, 2) # going to have to fix this for length of dictionary list
        self.rand_phrase = r.randrange(0, len(self.phrases[self.rand_key]))
        self.rand_dry = r.randrange(0,2)

        # Screen Item Location Variables.
        """
            Resolution Modifiers:
            480p : .667
            720 x 480 (pi zero w resolution) : .62
            720p : 1
            1080p : 1.5
            1440p : 2
            4k : 3
        """
        self.resolution_modifier = .62
        # Outer Borders and Margins
        self.right_left_border_mod = 20 * self.resolution_modifier
        self.title_margin_mod = 5 * self.resolution_modifier
        self.last_watered_top_mod = 50 * self.resolution_modifier
        self.phrase_bottom_mod = 150 * self.resolution_modifier
        # Left/Right Eye Position from Left
            # If changing resolution_modifier, might have to play around with these 
            # values to center eyes
        self.left_eye_edge = 220 * self.resolution_modifier
        self.right_eye_edge = 600 * self.resolution_modifier
        # Eye rect
        self.eye_rect_top = 200 * self.resolution_modifier
        self.eye_rect_width = 350 * self.resolution_modifier
        self.eye_rect_height = 150 * self.resolution_modifier
        # Eyelid Open
        self.eyelid_open_left_mod = 20 * self.resolution_modifier
        self.eyelid_open_right_mod = 330 * self.resolution_modifier
        self.eyelid_open_height = 240 * self.resolution_modifier
        # Pupils looking left
        self.pupil_left_mod = 50 * self.resolution_modifier
        self.pupil_height_left = 300 * self.resolution_modifier
        # Pupils looking right
        self.pupil_right_mod = 300 * self.resolution_modifier
        self.pupil_height_right = 300 * self.resolution_modifier
        # Pupils looking up
        self.pupil_height_up = 250 * self.resolution_modifier
        # Pupils looking straight
        self.pupil_straight_mod = 175 * self.resolution_modifier
        self.pupil_height_straight = 275 * self.resolution_modifier

        # Eye component line thickness
        self.eye_line_thickness = int(5 * self.resolution_modifier)
        self.pupil_size = 5
        self.eyelid_line_thickness = 2

        # Colors
        # Moisture
        self.moisture_value_color = (111, 194, 118)
        self.moisutre_title_color = (111, 194, 118)
        # Temperature
        self.temp_value_color = (125, 125, 125)
        self.temp_title_color = (125, 125, 125)
        # Eyes
        self.eye_outline_color = (125, 125, 125)
        self.eyelid_color = (125, 125, 125)
        self.pupil_color = (125, 125, 125)
        # Texts
        self.last_watered_color = (125, 125, 125)
        self.phrase_color = (125, 125, 125)

        # Font sizes and modifier
        self.font_size = int(120 * self.resolution_modifier)
        self.title_font_size = int(80 * self.resolution_modifier)
        self.text_font_size = int(70 * self.resolution_modifier)

        # Fonts for Pygame objects.
        self.font = pygame.font.SysFont(None, size=self.font_size)
        self.title_font = pygame.font.SysFont(None, size=self.title_font_size)
        self.text_font = pygame.font.SysFont(None, size=self.text_font_size)

    def run_program(self):
        """Sets up the main loop of the program."""
        while True:
            self._check_events()
            self._update_screen()
            self.blink_timer += 1
            self.pupil_timer += 1
            self.phrase_timer += 1
            self.clock.tick(10)

    def _check_events(self):
        """Check the input events from a user."""
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN: # Doesnt really make sense for touch screen...
                if event.key == pygame.K_q:
                    sys.exit()
    
    def _update_moisture_and_temp_values(self):
        try:
            moisture, temperature = self.sensor_client.get_values()
            self.moisture_value = int(moisture)
            self.temperature_value = temperature
            self.timeout_timer = 0
        except Exception as e:
            self.timeout_timer += 1
            print(f"{time.strftime('%H:%M:%S - %d/%b/%Y')} | Error: {e}")

            
    def _draw_moisture_value(self):
        """Draw the moisture value to the screen."""
        moisture_img = self.font.render(str(f'{self.moisture_value}%'), True, self.moisture_value_color)
        moisture_title = self.title_font.render("Moisture", True, self.moisutre_title_color)
        moisture_rect = moisture_img.get_rect()
        moisture_title_rect = moisture_title.get_rect()
        moisture_rect.center = self.screen_rect.center
        moisture_rect.left = self.screen_rect.left + self.right_left_border_mod
        moisture_title_rect.top = moisture_rect.bottom + self.title_margin_mod
        moisture_title_rect.left = self.screen_rect.left + self.right_left_border_mod
        self.screen.blits([(moisture_img, moisture_rect), (moisture_title, moisture_title_rect)])

    def _draw_soil_temp(self):
        """Draw the soil temperature to the screen."""
        temp_img = self.font.render(str(f"{self.temperature_value}\xb0F"), True, self.temp_value_color) # \xb0 Unicode for degree symbol
        temp_title = self.title_font.render("Temperature", True, self.temp_title_color)
        temp_rect = temp_img.get_rect()
        temp_title_rect = temp_title.get_rect()
        temp_rect.center = self.screen_rect.center
        temp_rect.right = self.screen_rect.right - self.right_left_border_mod
        temp_title_rect.top = temp_rect.bottom + self.title_margin_mod
        temp_title_rect.right = self.screen_rect.right - self.right_left_border_mod
        self.screen.blits([(temp_img, temp_rect), (temp_title, temp_title_rect)])

    def _draw_eye(self, left_edge):
        """Draw the eyes to the middle of the screen."""
        eye_rect = pygame.Rect(
                            left_edge, 
                            self.eye_rect_top, 
                            self.eye_rect_width, 
                            self.eye_rect_height
                            )
        pupil_loc = self._pupil_loc(left_edge)
        if self.blink_timer >= self.rand_blink_len + 1:
            self.blink_timer = 0
            self.rand_blink_len = r.randint(9, 16)
        if self.blink_timer < self.rand_blink_len:
            pygame.draw.ellipse(self.screen,
                                self.eye_outline_color,
                                eye_rect,
                                self.eye_line_thickness)
            pygame.draw.line(self.screen,
                             self.eyelid_color,
                             (left_edge + self.eyelid_open_left_mod, self.eyelid_open_height),
                             (left_edge + self.eyelid_open_right_mod, self.eyelid_open_height), 
                             self.eyelid_line_thickness)
            pygame.draw.circle(self.screen,
                               self.pupil_color,
                               pupil_loc,
                               self.pupil_size)
        if self.blink_timer == self.rand_blink_len:
            pygame.draw.ellipse(self.screen,
                                self.eye_outline_color,
                                eye_rect,
                                self.eye_line_thickness)
            pygame.draw.line(self.screen,
                            self.eyelid_color,
                            eye_rect.midleft,
                            eye_rect.midright,
                            self.eyelid_line_thickness)
    
    def _pupil_loc(self, left_edge):
        """Return the location of the pupil."""
        pupil_loc = [
                ((left_edge + self.pupil_left_mod), self.pupil_height_left), # Looking Left
                ((left_edge + self.pupil_right_mod), self.pupil_height_right), # Looking Right
                ((left_edge + self.pupil_straight_mod), self.pupil_height_up) # Looking Up
                ] 
        if self.pupil_timer >= self.rand_pup_len + 12:
                self.pupil_timer = 0
                self.rand_pup_loc = r.randrange(0,len(pupil_loc))
                self.rand_pup_len = r.randrange(15, 25)
        if self.pupil_timer <= self.rand_pup_len:
                return ((left_edge + self.pupil_straight_mod), self.pupil_height_straight) # Looking straight ahead
        if self.pupil_timer > self.rand_pup_len and self.pupil_timer < self.rand_pup_len + 12:
                return pupil_loc[self.rand_pup_loc]
        
    def _draw_last_water(self):
        """Draw the last time watering occured."""
        self.last_watered_list.append(self.moisture_value)
        if len(self.last_watered_list) > 5:
            self.last_watered_list.pop(0)
        if self.last_watered_list[-1] - self.last_watered_list[0] > 8:
            self.last_water_str = f"Last Water: {datetime.datetime.now().strftime('%m/%d/%Y, %I:%M %p')}"
        last_water_img = self.text_font.render(self.last_water_str, True, self.last_watered_color)
        last_water_img_rect = last_water_img.get_rect()
        last_water_img_rect.center = self.screen_rect.center
        last_water_img_rect.top = self.screen_rect.top + self.last_watered_top_mod
        self.screen.blit(last_water_img, last_water_img_rect)
    
    def _draw_phrase(self):
        phrase_str = self._choose_phrase()
        phrase_img = self.text_font.render(phrase_str, True, self.phrase_color)
        phrase_rect = phrase_img.get_rect()
        phrase_rect.center = self.screen_rect.center
        phrase_rect.bottom = self.screen_rect.bottom - self.phrase_bottom_mod
        self.screen.blit(phrase_img, phrase_rect)

    def _choose_phrase(self):
        """Return the phrase the will be drawn to the screen."""
        if self.phrase_timer >= self.rand_phrase_len + 12:
            self.phrase_timer = 0
            self.rand_phrase_len = r.randrange(6, 11) # How long before phrase appears
            self.rand_key = r.randrange(0,2) # Which key to use in dictionary
            self.rand_phrase = r.randrange(0, len(self.phrases[self.rand_key])) # Which List entry in dictionary
            self.rand_dry = r.randrange(0,2)
            return None
        elif self.timeout_timer >= 5:
            phrase_str = 'Sensor Error: Please power cycle sensor!'
            return phrase_str
        elif self.moisture_value >= 80:
            phrase_str = (self.phrases[self.rand_key][self.rand_phrase])
            return phrase_str
        else:
            phrase_str = (self.phrases[2][self.rand_dry])
            return phrase_str

    def _update_screen(self):
        """Update the screen with all elements."""
        if time.localtime().tm_hour == 3: # Change this eventually to be for a shorter time than 1 hr
            self.screen.blit(self.secret_bg, (0, 0))
        else:
            self.screen.blit(self.bg, (0, 0))
        #start = time.time()
        self._update_moisture_and_temp_values()
        #print(f"Update time: {time.time() - start}")
        self._draw_moisture_value()
        self._draw_soil_temp()
        self._draw_eye(self.left_eye_edge) # Left Eye
        self._draw_eye(self.right_eye_edge) # Right Eye
        self._draw_last_water()
        if self.timeout_timer >= 5:
            self._draw_phrase()
        elif self.phrase_timer >= self.rand_phrase_len:
            self._draw_phrase()
        pygame.display.flip()

if __name__ == '__main__':
    print('This version is designed for the pico w.')
    wm = WaterMeLite()
    wm.run_program()