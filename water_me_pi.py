import sys
import datetime
import calendar
import time
import board

from pathlib import Path
import json
import pygame
from adafruit_seesaw.seesaw import Seesaw

import weather as w

class WaterMe:
    """"Defines the overall class of the program."""

    def __init__(self):
        """Initialize the program and create resources."""
        # Sensor data input.
        i2c_bus = board.I2C()
        self.ss = Seesaw(i2c_bus, addr=0x36)
        self.temp = self.ss.get_temp()

        # Display Initialize
        pygame.init()
        pygame.mouse.set_visible(False)
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((480,320), pygame.NOFRAME)
        self.screen_rect = self.screen.get_rect()
        self.bg_color = (255, 255, 255)
        self.text_color = (30, 30, 67)
        self.font = pygame.font.SysFont(None,  22)
        self.m_font = pygame.font.SysFont(None,  75)
        self.mt_font = pygame.font.SysFont(None, 55)

        # Create required Paths.
        self.path = Path('moisture.png')
        self.path_w = Path('weather.json')

        self.weather = self._retrieve_weather()
        self.w_days = self.weather['days']
        self.full_forecast = self._generate_forecast()
        self.dates = []
        for key in self.full_forecast.keys():
            self.dates.append(key)
        self.forecast = []
        for value in self.full_forecast.values():
            self.forecast.append(value)
        self.icons = []
        for i in range(len(self.w_days)):
            day = self.w_days[i]
            icon = day['icon']
            self.icons.append(icon)
        
        self.date = str(datetime.date.today()) 
        self.optimal_moist = 100
        self.m_values = []
        self.last_water_str = "Waiting for watering..."

        self.sad = pygame.image.load('images/sad.png')
        self.neutral = pygame.image.load('images/neutral.png')
        self.happy = pygame.image.load('images/happy.png')
        
    def run_program(self):
        """Run the program."""
        while True:
            #start_time = time.time()
            self.moisture = self._generate_moisture_avg()
            self._generate_weather()
            self._update_screen()
            self._check_events()
            self.clock.tick()
            #print("percent out: %.2f" % (time.time() - start_time))

    def _check_events(self):
        """Check for input to close the program."""
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    sys.exit()
    
    def _generate_moisture_avg(self): # Generating the list takes .67 of the .73 second frames
        """Generate an average value of 'poll_num' readings."""
        poll_num = 50
        moisture_list = []
        for i in range(poll_num):
            moisture_list.append(self.ss.moisture_read()) # Moisture from sensor reading
        moisture = int(((sum(moisture_list) / poll_num) / 1000) * 100)
        return moisture

    def _generate_weather(self):
        """Make API call to update weather.json."""
        self.date = str(datetime.date.today())
        if str(self.dates[0]) != str(self.date):
            w.generate_weather()
            self.weather = self._retrieve_weather()
            self.w_days = self.weather['days']
            self.full_forecast = self._generate_forecast()
            self.dates = []
            for key in self.full_forecast.keys():
                self.dates.append(key)
            self.forecast = []
            for value in self.full_forecast.values():
                self.forecast.append(value)
            self.icons = []
            for i in range(len(self.w_days)):
                day = self.w_days[i]
                icon = day['icon']
                self.icons.append(icon)

    def _retrieve_weather(self):
        """Retrieve weather data from json file."""
        contents = self.path_w.read_text()
        weather = json.loads(contents)
        return weather
    
    def _generate_forecast(self):
        """Generate the forecast."""
        forecast = {}
        for i in range(len(self.w_days)):
            day = self.w_days[i]
            date = day['datetime']
            temp = day['temp']
            forecast[date] = temp
        return forecast

    def _choose_moisture_emotions(self, moist):
        """Choose emotions depending on moisture level."""
        if moist < self.optimal_moist - (int(self.optimal_moist*.25)) or moist > self.optimal_moist + (int(self.optimal_moist*.25)): # Do not need the greater than lines.
            self.moist_img = self.m_font.render(self.moist_str, True, 
                                                (225,80,90))
            self.img = self.sad
            self.phrase_img = self.mt_font.render("I'm DRY!", True, self.text_color)
        elif moist < self.optimal_moist - (int(self.optimal_moist*.1)) or moist > self.optimal_moist + (int(self.optimal_moist*.1)): # Do not need the greater than lines.
            self.moist_img = self.m_font.render(self.moist_str, True, 
                                                (255,192,0))
            self.img = self.neutral
            self.phrase_img = self.mt_font.render("I'm damp.", True, self.text_color)
        else:
            self.moist_img = self.m_font.render(self.moist_str, True, 
                                                (111,194,118))
            self.img = self.happy
            self.phrase_img = self.mt_font.render("I'm wet...", True, self.text_color)

    def _draw_moisture_title(self):
        """Draw the moisture title to the screen."""
        moist_title = "Hydration"
        self.moist_title_img = self.mt_font.render(moist_title, True, 
                                                   (25, 150, 230))
        self.moist_title_rect = self.moist_title_img.get_rect()
        self.moist_title_rect.left = self.screen_rect.left + 20
        self.moist_title_rect.top = 30
        self.screen.blit(self.moist_title_img, self.moist_title_rect)

    def _draw_moisture_num(self):
        """Draw the moisture number to the screen."""
        self.moist_str = str(f"{self.moisture}%")
        self._choose_moisture_emotions(self.moisture)        
        self.moist_rect = self.moist_img.get_rect()
        self.moist_rect.center = self.moist_title_rect.center
        self.moist_rect.top = self.moist_title_rect.bottom + 10
        self.screen.blit(self.moist_img, self.moist_rect)
    
    def _draw_image(self):
        """Choose the image depending on moisture level."""
        # Pulls img value from _draw_moisture_number -> _Choose_moisture_emotion
        self.img_rect = self.img.get_rect()
        self.img_rect.top = self.c_temp_rect.bottom
        self.img_rect.left = self.date_rect.left + 20
        self.screen.blit(self.img, self.img_rect)
    
    def _draw_phrase(self):
        """Draw the phrase to be displayed."""
        self.phrase_rect = self.phrase_img.get_rect()
        self.phrase_rect.y = self.img_rect.y + 100
        self.phrase_rect.right = self.img_rect.left - 25
        self.screen.blit(self.phrase_img, self.phrase_rect)
 
    def _draw_date_time(self):
        """Draw the date and time to the screen."""
        self.now = datetime.datetime.now()
        weekday = calendar.day_name[self.now.weekday()]
        self.datetime = f"{weekday}, {str(self.now.strftime('%m/%d/%Y, %I:%M %p'))}"
        self.date_img = self.font.render(self.datetime, True, self.text_color)
        self.date_rect = self.date_img.get_rect()
        self.date_rect.right = self.screen_rect.right - 55
        self.date_rect.top = 20
        self.screen.blit(self.date_img, self.date_rect)
    
    def _draw_location(self):
        """Draw the city and state to the screen."""
        location = self.weather['address']
        loc_str = f"{location}"
        self.location_img = self.font.render(loc_str, True,
                                        self.text_color)
        self.location_rect = self.location_img.get_rect()
        self.location_rect.top = self.date_rect.bottom + 10
        self.location_rect.left = self.date_rect.left
        self.screen.blit(self.location_img, self.location_rect)
    
    def _draw_current_temp(self):
        """Draw current weather to the screen."""
        i = 0
        self.c_time = self.now.strftime('%H:00:00')
        for day in range(len(self.w_days)):
            day = self.w_days[i]
            i += 1
            if self.date == day['datetime']:
                hours = day['hours']
                h = 0
                for hour in range(len(hours)):
                    hour = hours[h]
                    h += 1
                    if self.c_time == hour['datetime']:
                        temp = hour['temp']
                        feel = hour['feelslike']
                        self.c_icon = hour['icon']
                        temp_str = f"Current Temp: {temp}, Feels like: {feel}"
                        self.c_temp_img = self.font.render(temp_str, True, 
                                                        self.text_color)
                        self.c_temp_rect = self.c_temp_img.get_rect()
                        self.c_temp_rect.top = self.location_rect.bottom + 10
                        self.c_temp_rect.left = self.location_rect.left
                        self.screen.blit(self.c_temp_img, self.c_temp_rect)
                    else:
                        continue
            else:
                continue
        
    def _draw_current_icon(self):
        """Draws the current weather icon to the screen."""
        # Creates self.c_icon list from hour dict in _draw_current_temp()
        c_icon_format = f"images/{self.c_icon}.png"
        #try:
        c_icon = pygame.image.load(c_icon_format)
        #except pygame.error:
        #    c_icon = pygame.image.load('images/partly-cloudy-day.png')
        c_icon = pygame.transform.scale(c_icon, (40,40))
        c_icon_rect = c_icon.get_rect()
        c_icon_rect.y = 15
        c_icon_rect.right = self.screen_rect.right - 10
        self.screen.blit(c_icon, c_icon_rect)
    
    def _draw_date_forecast(self):
        """Draw the 5 day forecast."""
        f = 0
        for i in range(1, 6):
            day = datetime.datetime.strptime(self.dates[(i)], '%Y-%m-%d')
            five_day = (f"{calendar.day_name[day.weekday()]}")
            self.five_day_img = self.font.render(five_day, True, self.text_color)
            self.five_day_rect = self.five_day_img.get_rect()
            self.five_day_rect.x = (18+(f*10)) + (80*f+(6*f))
            self.five_day_rect.bottom = self.screen_rect.bottom - 50
            self.screen.blit(self.five_day_img, self.five_day_rect)
            f += 1
    
    def _draw_forecast(self):
        """Draw the 5 day forecast."""
        f = 0
        for i in range(1,6):
            forecast_str = f"{self.forecast[i]} F"
            self.forecast_img = self.font.render(forecast_str, True, self.text_color)
            self.forecast_rect = self.forecast_img.get_rect()
            self.forecast_rect.x = (25+(f*25)) + ((70*f)+5)
            self.forecast_rect.top = self.five_day_rect.bottom + 5
            self.screen.blit(self.forecast_img, self.forecast_rect)
            f += 1
    
    def _draw_weekly_icons(self):
        """Generate the weekly icon list."""
        for i in range(0,5):
            icon = self.icons[i]
            icon_format = f"images/{icon}.png"
            try:
                icon_img = pygame.image.load(icon_format)
            except pygame.error:
                icon_img = pygame.image.load('images/partly-cloudy-day.png')
            icon_img = pygame.transform.scale(icon_img, (25,25))
            icon_img_rect = icon_img.get_rect()
            icon_img_rect.x = (30+(i*7)) + (90*i)
            icon_img_rect.bottom = self.screen_rect.bottom - 5
            self.screen.blit(icon_img, icon_img_rect)
            
    def _draw_last_water(self):
        """Draw the date and time of last water."""
        self.m_values.append(self.moisture)
        if len(self.m_values) > 5:
            self.m_values.pop(0)
            value_1 = self.m_values[0]
            value_2 = self.m_values[4]
            if value_2 > int(value_1 + (int(value_1)*.1)):
                self.last_water_str = f"Last Water: {str(self.now.strftime('%m-%d-%Y'))}"

        self.last_water_img = self.font.render(self.last_water_str, True, self.text_color)
        self.last_water_rect = self.last_water_img.get_rect()
        self.last_water_rect.center = self.moist_title_rect.center
        self.last_water_rect.top = self.moist_rect.bottom + 10
        self.screen.blit(self.last_water_img, self.last_water_rect)

    def _update_screen(self):
        """Draw the screen with the graph and information."""
        self.screen.fill(self.bg_color)
        self._draw_moisture_title()
        self._draw_moisture_num()
        self._draw_date_time()
        self._draw_location()
        self._draw_current_temp()
        self._draw_current_icon()
        self._draw_last_water()
        self._draw_date_forecast()
        self._draw_forecast()
        self._draw_weekly_icons()
        self._draw_image()
        self._draw_phrase()
        pygame.display.flip()

if __name__ == '__main__':

    w.generate_weather()
    waterme = WaterMe()
    waterme.run_program()

