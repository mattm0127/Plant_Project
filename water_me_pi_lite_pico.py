import datetime

# from adafruit_seesaw.seesaw import Seesaw
import random as r
import socket
import sys
import time
import traceback
import threading

import pygame
import requests


class RequestIDError(Exception):
    """Exception for ID Sent/Receive mismatch.

    Args:
        Exception (Exception): Returns a String for ID mismatch error.
    """
    def __init__(self, return_request_id):
        self.message = "Request/Response ID's do not match."
        self.return_request_id = return_request_id

    def __str__(self):
        return self.message


class SensorHTTPClient:
    """HTTP Client to send/receive requests from Sensor Server 

    Returns:
        str: Sensor server Data.
    """
    BASE_URL = "http://"
    TIMEOUT_VALUE = 0.06
    HTTP_IP = "192.168.4.1"
    HTTP_PORT = 5000

    def __init__(self):
        None

    def _sensor_request(self, request_type, sensor_data_request, data=None):
        """Sends the request to the sensor server.

        Args:
            request_type (str): HTTP Request type (GET/POST)
            sensor_data_request (str): Endpoint for server request
            data (str, optional): Data to be sent to server (POST requests Only). Defaults to None.

        Returns:
            str: String containing server responses
        """
        url = f"{self.BASE_URL}{self.HTTP_IP}:{self.HTTP_PORT}/{sensor_data_request}"

        if request_type.upper() == "GET":
            try:
                response = requests.get(url, timeout=self.TIMEOUT_VALUE)
                value = response.text
                return value
            except requests.exceptions.RequestException as e:
                print(f"Error: {e}")

        if request_type.upper() == "POST":
            try:
                response = requests.post(url=url, data=data)
                sensor_ip_address = response.text
                return sensor_ip_address
            except requests.exceptions.RequestException as e:
                print(f"Error: {e}")

    def send_wifi_credentials(self):
        """Send Host WiFI Credentials to Sensor Server.

        Returns:
            str: WiFi IP Address of sensor server.
        """
        data = {"SSID": "...They Will Come", "SSID_PASSWORD": "55hudson1n"}
        sensor_ip_address = self._sensor_request("post", "credentials", data=data)
        return sensor_ip_address

    def get_values(self):

        combined_values = self._sensor_request("get", "moisture-temperature")
        return combined_values.split(",")

    def get_moisture_value(self):
        moisture_value = self._sensor_request("get", "moisture")
        return moisture_value

    def get_temperature_value(self):
        temperature_value = self._sensor_request("get", "temperature")
        return temperature_value


class SensorUDPClient:
    """UDP Client to receive values from Sensor Server.

    Returns:
        Moisture and Temperature values in a list.
    """

    TIMEOUT_VALUE = 0.1

    def __init__(self, udp_ip_address: str, port: int):
        """Initialize the variables needed to connect to the UDP Server.    

        Args:
            udp_ip_address (str): IP Address of the UDP Host
            port (int): Port the UDP Server is listening on
        """
        self.udp_host_name = "Money Tree"
        self.udp_host_ip = udp_ip_address
        self.udp_host_port = port
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.settimeout(self.TIMEOUT_VALUE)

    def get_values(self):
        """Requests values from the sensor and ensure matching results.
        """
        def _get_request_id():
            """Generates random request_id

            Returns:
                int: Random request_id assigned to outgoing requests.
            """
            return r.randint(0, 100_000)
        
        def _send_request(request_id):
            """Sends the request to the sensor.

            Args:
                request_id (int): unique request id for identifying requests/responses

            Returns:
                request_id (int): the request_id of the outgoing request.
            """
            if self.udp_socket.fileno() == -1: # Indicates that the socket is closed
                self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.udp_socket.settimeout(self.TIMEOUT_VALUE)
            self.udp_socket.sendto(
                f"{request_id}:request_data".encode(),
                (self.udp_host_ip, self.udp_host_port),
            )
            return request_id
        
        def _receive_data(request_id):
            """Process the data received from the sensor.

            Args:
                request_id (int): the expected request_id of the incoming request 

            Raises:
                RequestIDError: Raised if request/response IDs do not match

            Returns:
                [moisture, temperature]: List containing the moisture and temperature values from the sensor.
            """
            data, addr = self.udp_socket.recvfrom(1024)
            decoded_data = data.decode()
            return_request_id, return_data = decoded_data.split(":")
            print(f"Request ID: {return_request_id} - Returned in : {time.time()-start}")
            if int(return_request_id) == request_id:
                return return_data.split(",")
            else:
                raise RequestIDError(return_request_id)

        try:
            start = time.time()
            request_id = _send_request(request_id=_get_request_id())
            print(f"Sent Request ID : {request_id}")
            return _receive_data(request_id=request_id)
        except socket.timeout:
            print(
                f"Sensor: {self.udp_host_name} @ {time.strftime('%H:%M:%S - %d/%b/%Y')} | Error: Socket Time Out, Retrying..."
            )
            try:
                return _receive_data(request_id=request_id)
            except socket.timeout:
                print(
                    f"Sensor: {self.udp_host_name} @ {time.strftime('%H:%M:%S - %d/%b/%Y')} | Error: Socket Timed Out, Resetting Socket"
                )
                self.udp_socket.close()
        except RequestIDError as e:
            print(
                f"Sensor: {self.udp_host_name} @ {time.strftime('%H:%M:%S - %d/%b/%Y')} | Error: {e}, Sent:{request_id} Returned:{e.return_request_id}. Retrying..."
            )
            try:
                time.sleep(0.1)
                return _receive_data(request_id=request_id)
            except Exception:
                self.udp_socket.close()
        except Exception as e:
            print(
                f"Sensor: {self.udp_host_name} @ {time.strftime('%H:%M:%S - %d/%b/%Y')} | Error: {e}"
            )
            traceback.print_exc()

    def send_reset(self):
        """Sends reset request to Sensor Server incase of errors.
        """
        self.udp_socket.sendto("reset".encode(), (self.udp_host_ip, self.udp_host_port))

# Have it look too see if there is a value in the buffer, if so grab it, request a new one
# timeout so the program is quick. If no buffer and request is longer than a short time
# timeout and keep going, and send another request. 
class WaterMeLite:
    """The main class for the WaterMeLite project."""

    FRAME_DELAY = 0.150

    def __init__(self, udp_ip_address):
        """Initializes the main variables for the WaterMe Display

        Args:
            udp_ip_address (str): IP Address of the Host UDP Server.

        """

        # Create the sensor data.
        self.sensor_client = SensorUDPClient(udp_ip_address=udp_ip_address, port=1900)
        self.sensor_timeout = 0
        self.data_lock = threading.Lock()

        # Initiate pygame display.
        pygame.init()
        pygame.mouse.set_visible(False)
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((1280, 720), pygame.NOFRAME)
        self.screen_rect = self.screen.get_rect()
        background = pygame.image.load("images/bg_2.jpg")
        self.background = pygame.transform.scale(background, (self.screen.get_size()))
        secret_background = pygame.image.load("images/magic_horse.jpg")
        self.secret_background = pygame.transform.scale(
            secret_background, (self.screen.get_size())
        )
        self.dirty_rects = []

        # Global Lists and strings.
        
        self.moisture_value = 0
        self.temperature_value = 0
        self.previous_moisture_title_rect = None
        self.previous_temperature_title_rect = None
        self.last_watered_list = []
        self.last_water_string = "Waiting for Water..."
        self.previous_last_water_rect = None
        self.phrase_string = ""
        self.previous_phrase_rect = None
        self.random_phrase_key = ""
        self.previous_phrase_title_rect = None

        # Database for responses to system condition.
        self.phrases = {
            # Plant lines
            self.sensor_client.udp_host_name: [
                "I'm nice and moist.",
                "I'm all filled up for now.",
                "I'm cleaning the air for you...you're welcome.",
                "Take care of me and there is a chance I bloom.",
                "If one group has 6 leaves, you're lucky.",
                "If one group has 7 leaves, you're even luckier.",
                "I filter Xylene, Benzene and more from the air.",
                "My 5 Leaves: Metal, Wind, Fire, Water and Earth.",
            ],
            # Neutral facts
            "Neutral Facts": [
                "Banana is actually an Arabic word for fingers.",
                "Oak trees start producing acorns at 50 years old.",
                "Apples, onions and potatoes have the same taste.",
                "Around 70,000 plants are used in medicine.",
                "Dandelions can be eaten whole, all of it.",
                "Chemicals from cut grass can relieve stress.",
                "85% of all plantlife is found in the ocean.",
                "Plants communicate through roots with chemicals.",
            ],
            # Dry lines
            "Dry Lines": [
                "I haven't been filled up in awhile.",
                "Please make me wet.",
                "Are you trying to kill me?",
            ],
        }

        # Global Timers and randoms for various changes.
        self.blink_timer = 0
        self.time_to_blink = r.randint(9, 16)
        self.pupil_timer = 0
        self.pupil_move_length = r.randrange(15, 25)  # Same as above
        self.pupil_location = r.randrange(
            0, 3
        )  # Determines the random location pupil is looking

        self.phrase_keys_list = list(enumerate(self.phrases.keys()))
        self.phrase_timer = 0
        self.phrase_end = 12
        self.phrase_pause = r.randrange(6, 11)
        self.key_index = r.randrange(
            0, 2
        )  # going to have to fix this for length of dictionary list

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
        self.resolution_modifier = 1
        # Outer Borders and Margins
        self.right_left_border_mod = 20 * self.resolution_modifier
        self.title_margin_mod = 5 * self.resolution_modifier
        self.last_watered_top_mod = 50 * self.resolution_modifier
        self.phrase_title_bottom_mod = 220 * self.resolution_modifier
        self.phrase_bottom_mod = 120 * self.resolution_modifier

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
        self.moisture_value_color_moist = (111, 194, 118)
        self.moisture_value_color_dry = (238, 97, 16)
        self.moisture_title_color = (125, 125, 125)
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
        """Initiates the main loop of the program."""

        def _increment_timers():
            self.blink_timer += 1
            self.pupil_timer += 1
            self.phrase_timer += 1

        while True:
            try:
                self._check_events()
                #self._update_moisture_and_temp_values()
                self._update_screen()
                _increment_timers()
                self.clock.tick(10)
                print(self.clock.get_fps())
                # print(time.time()-frame_delay_start)
            except Exception as e:
                print(
                    f"Main Loop @ {time.strftime('%H:%M:%S - %d/%b/%Y')} | Exception: {e}"
                )
                traceback.print_exc()

    def sensor_thread(self):
        sens_thread = threading.Thread(
            target=self._update_moisture_and_temp_values, 
            daemon=True
            )
        sens_thread.start()

    def _check_events(self):
        """Check the input events from a user."""
        for event in pygame.event.get():
            if (
                event.type == pygame.KEYDOWN
            ):  # Doesnt really make sense for touch screen...
                if event.key == pygame.K_q:
                    sys.exit()

    def _update_moisture_and_temp_values(self):
        """Initiates the sensor client to get moisture and temperature values.
        """
        while True:
            if self.sensor_timeout != 0 and self.sensor_timeout % 100 == 0:
                try:
                    self.sensor_client.send_reset()
                    time.sleep(5)
                except Exception as e:
                    print(
                        f"Sensor Reset Attempt @ {time.strftime('%H:%M:%S - %d/%b/%Y')} | Error: {e}"
                    )
                    traceback.print_exc()
            try:
                moisture, temperature = self.sensor_client.get_values()
                with self.data_lock:
                    self.moisture_value = int(moisture)
                    self.temperature_value = temperature
                self.sensor_timeout = 0
            except TypeError:
                self.sensor_timeout += 1
            except Exception as e:
                self.sensor_timeout += 1
                print(
                    f"Data Values Update @ {time.strftime('%H:%M:%S - %d/%b/%Y')} | Error: {e}"
                )
                traceback.print_exc()
            time.sleep(5)

    def _draw_moisture_value(self):
        """Draw the moisture value to the screen."""

        def _get_moisture_value_color():
            """Selects the appropriate color for the moisture value depending on
            the moisture value.

            Returns:
                (int,int,int): Color Value
            """
            if self.moisture_value < 80:
                return self.moisture_value_color_dry
            return self.moisture_value_color_moist
        
        with self.data_lock:
            moisture_img = self.font.render(
                str(f"{self.moisture_value}%"), True, _get_moisture_value_color()
            )
        moisture_title = self.title_font.render(
            self.sensor_client.udp_host_name, True, self.moisture_title_color
        )
        moisture_rect = moisture_img.get_rect()
        moisture_title_rect = moisture_title.get_rect()
        moisture_rect.center = self.screen_rect.center
        moisture_rect.left = self.screen_rect.left + self.right_left_border_mod
        moisture_title_rect.top = moisture_rect.bottom + self.title_margin_mod
        moisture_title_rect.left = self.screen_rect.left + self.right_left_border_mod
        self.screen.blits(
            blit_sequence=[
                (moisture_img, moisture_rect),
                (moisture_title, moisture_title_rect),
            ]
        )
        if self.previous_moisture_title_rect != moisture_title_rect:
            self.dirty_rects.extend([moisture_rect, moisture_title_rect])
            self.previous_moisture_title_rect = moisture_title_rect
        else:
            self.dirty_rects.append(moisture_rect)

    def _draw_soil_temp(self):
        """Draw the soil temperature to the screen."""
        with self.data_lock:
            temp_img = self.font.render(
                str(f"{self.temperature_value}\xb0F"), True, self.temp_value_color
            )  # \xb0 Unicode for degree symbol
        temp_title = self.title_font.render("Temperature", True, self.temp_title_color)
        temp_rect = temp_img.get_rect()
        temp_title_rect = temp_title.get_rect()
        temp_rect.center = self.screen_rect.center
        temp_rect.right = self.screen_rect.right - self.right_left_border_mod
        temp_title_rect.top = temp_rect.bottom + self.title_margin_mod
        temp_title_rect.right = self.screen_rect.right - self.right_left_border_mod
        self.screen.blits(
            blit_sequence=[(temp_img, temp_rect), (temp_title, temp_title_rect)]
        )
        if self.previous_temperature_title_rect != temp_title_rect:
            self.dirty_rects.extend([temp_rect, temp_title_rect])
            self.previous_temperature_title_rect = temp_title_rect
        else:
            self.dirty_rects.append(temp_rect)

    def _draw_eye(self, left_edge):
        """Draw the eyes to the middle of the screen."""

        def _get_pupil_location(left_edge):
            """Applies random timers to determine pupil location on screen.

            Args:
                left_edge (int): Position from the left edge of the screen.

            Returns:
                (float,float): Tuple of Coordinate location for the pupil
            """
            pupil_loc = [
                (
                    (left_edge + self.pupil_left_mod),
                    self.pupil_height_left,
                ),  # Looking Left
                (
                    (left_edge + self.pupil_right_mod),
                    self.pupil_height_right,
                ),  # Looking Right
                (
                    (left_edge + self.pupil_straight_mod),
                    self.pupil_height_up,
                ),  # Looking Up
            ]
            if self.pupil_timer >= self.pupil_move_length + 12:
                self.pupil_timer = 0
                self.pupil_location = r.randrange(0, len(pupil_loc))
                self.pupil_move_length = r.randrange(15, 25)
            if self.pupil_timer <= self.pupil_move_length:
                return (
                    (left_edge + self.pupil_straight_mod),
                    self.pupil_height_straight,
                )  # Looking straight ahead
            if (
                self.pupil_timer > self.pupil_move_length
                and self.pupil_timer < self.pupil_move_length + 12
            ):
                return pupil_loc[self.pupil_location]

        eye_rect = pygame.Rect(
            left_edge, self.eye_rect_top, self.eye_rect_width, self.eye_rect_height
        )
        pupil_loc = _get_pupil_location(left_edge)

        if self.blink_timer >= self.time_to_blink + 1:
            self.blink_timer = 0
            self.time_to_blink = r.randint(9, 16)
        if self.blink_timer < self.time_to_blink:
            pygame.draw.ellipse(
                self.screen, self.eye_outline_color, eye_rect, self.eye_line_thickness
            )
            pygame.draw.line(
                self.screen,
                self.eyelid_color,
                (left_edge + self.eyelid_open_left_mod, self.eyelid_open_height),
                (left_edge + self.eyelid_open_right_mod, self.eyelid_open_height),
                self.eyelid_line_thickness,
            )
            pygame.draw.circle(
                self.screen, self.pupil_color, pupil_loc, self.pupil_size
            )
        if self.blink_timer == self.time_to_blink:
            pygame.draw.ellipse(
                self.screen, self.eye_outline_color, eye_rect, self.eye_line_thickness
            )
            pygame.draw.line(
                self.screen,
                self.eyelid_color,
                eye_rect.midleft,
                eye_rect.midright,
                self.eyelid_line_thickness,
            )
        self.dirty_rects.append(eye_rect)

    def _draw_last_water(self):
        """Draw the last time watering occured."""
        with self.data_lock:
            self.last_watered_list.append(self.moisture_value)
        if len(self.last_watered_list) > 5:
            self.last_watered_list.pop(0)
        if (
            len(self.last_watered_list) == 5
            and self.last_watered_list[-1] - self.last_watered_list[0] > 8
        ):
            self.last_water_string = (
                f"Last Water: {datetime.datetime.now().strftime('%m/%d/%Y, %I:%M %p')}"
            )
        last_water_img = self.text_font.render(
            self.last_water_string, True, self.last_watered_color
        )
        last_water_img_rect = last_water_img.get_rect()
        last_water_img_rect.center = self.screen_rect.center
        last_water_img_rect.top = self.screen_rect.top + self.last_watered_top_mod
        self.screen.blit(last_water_img, last_water_img_rect)
        if self.previous_last_water_rect != last_water_img_rect:
            self.dirty_rects.append(last_water_img_rect)
            self.previous_last_water_rect = last_water_img_rect

    def _draw_phrase(self):
        """Draw the phrase to the screen."""
        self._update_phrase()
        phrase_img = self.text_font.render(self.phrase_string, True, self.phrase_color)
        phrase_title = self.text_font.render(
            self.random_phrase_key, True, self.phrase_color
        )
        phrase_rect = phrase_img.get_rect()
        phrase_title_rect = phrase_title.get_rect()
        phrase_title_rect.center = self.screen_rect.center
        phrase_title_rect.bottom = (
            self.screen_rect.bottom - self.phrase_title_bottom_mod
        )
        phrase_rect.center = self.screen_rect.center
        phrase_rect.bottom = self.screen_rect.bottom - self.phrase_bottom_mod
        self.screen.blits(
            blit_sequence=[(phrase_title, phrase_title_rect), (phrase_img, phrase_rect)]
        )
        if self.previous_phrase_title_rect != phrase_title_rect:
            self.dirty_rects.append(phrase_title_rect)
            self.previous_phrase_title_rect = phrase_title_rect
        if self.previous_phrase_rect != phrase_rect:
            self.dirty_rects.append(phrase_rect)
            self.previous_phrase_rect = phrase_rect

    def _update_phrase(self):
        """Set the phrase that will be drawn to the screen."""
        if self.phrase_timer >= self.phrase_pause + self.phrase_end:
            self.phrase_timer = 0
            self.phrase_string = ""
            self.random_phrase_key = ""
            self.phrase_pause = r.randrange(6, 11)  # How long before phrase appears
            self.key_index = r.randrange(0, 2)  # Which key to use in dictionary

        elif self.sensor_timeout >= 40:
            self.phrase_string = "Sensor Error: Please Uplug and Plug Back In"

        elif self.sensor_timeout >= 20:
            self.phrase_string = "Sensor Error: Attempting Reset!"

        elif self.phrase_timer == self.phrase_pause:
            with self.data_lock:
                if self.moisture_value >= 80:
                    self.random_phrase_key = self.phrase_keys_list[self.key_index][1]
                    random_phrase_id = r.randrange(
                        0, len(self.phrases[self.random_phrase_key])
                    )  # Which List entry in dictionary
                    self.phrase_string = self.phrases[self.random_phrase_key][
                        random_phrase_id
                    ]
                else:
                    random_dry_phrase_id = r.randrange(0, len(self.phrases["Dry Lines"]))
                    self.phrase_string = self.phrases["Dry Lines"][random_dry_phrase_id]
                    self.random_phrase_key = "..."

    def _update_screen(self):
        """Update the screen with all the dirty rects."""
        try:
            #start = time.time()
            if (
                time.localtime().tm_hour == 3
            ):  # Change this eventually to be for a shorter time than 1 hr
                self.screen.blit(self.secret_background, (0, 0))
                self.dirty_rects.append(self.screen_rect)
            else:
                self.screen.blit(self.background, (0, 0))
                self.dirty_rects.append(self.screen_rect)
            self._draw_moisture_value()
            self._draw_soil_temp()
            self._draw_eye(self.left_eye_edge)  # Left Eye
            self._draw_eye(self.right_eye_edge)  # Right Eye
            self._draw_last_water()
            self._draw_phrase()
            pygame.display.update(self.dirty_rects)
            self.dirty_rects = []
            #print(f"Display Done: {time.time()-start}")
        except Exception as e:
            print(
                f"Screen Update @ {time.strftime('%H:%M:%S - %d/%b/%Y')} | Exception: {e}"
            )
            traceback.print_exc()

if __name__ == "__main__":
    print("This version is designed for the pico w.")
    pico_udp_ip_address = "192.168.86.26"
    wm = WaterMeLite(udp_ip_address=pico_udp_ip_address)
    wm.sensor_thread()
    wm.run_program()
