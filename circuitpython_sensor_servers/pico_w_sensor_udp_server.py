import os
import wifi
import socketpool
import board
import busio
import time
import microcontroller
from adafruit_seesaw.seesaw import Seesaw

class SensorController:
    
    def __init__(self, ssid, ssid_password, i2c_address, i2c_bus, udp_port):
        self.sensor = Seesaw(i2c_bus, i2c_address)
        self.ssid = ssid
        self.ssid_password = ssid_password
        self.udp_host = None
        self.udp_port = udp_port
        self.pool = None
        self.sock = None
        self.moisture_value = int(self.sensor.moisture_read() / 10)
        self.temperature = int(((self.sensor.get_temp() * 9) / 5) + 32)
        
    def _initiate_server_variables(self):
        self.udp_host = str(wifi.radio.ipv4_address)
        self.pool = socketpool.SocketPool(wifi.radio)
        
    def connect_wifi_radio(self):
        # Connect to Wi-Fi
        print("Connecting to Wifi...")
        wifi.radio.connect(self.ssid, self.ssid_password)
        self._initiate_server_variables()
        print("Connected to WiFi")
        print(f"My IP address is {self.udp_host}")
        
    def reset_wifi_radio(self):
        print("Re-connecting to Wifi...")
        wifi.radio.enabled = False
        self.sock.close()
        wifi.radio.enabled = True
        wifi.radio.connect(self.ssid, self.ssid_password)
        print("Re-Connected to WiFi")
        print(f"My IP address is {self.udp_host}")
        
    def reset_sensor(self):
        time.sleep(1)
        print("Restarting...")
        microcontroller.reset()
    
    def initiate_udp_server(self):
        # Initiate the Server for data communication.
        print("Initiating UDP Server...")
        self.sock = self.pool.socket(self.pool.AF_INET, self.pool.SOCK_DGRAM)
        self.sock.bind((self.udp_host, self.udp_port))
        print(f"UDP Server Created on {self.udp_host}, listening for requests on: {self.udp_port}")
        
    def generate_new_sensor_values(self):
        moisture_list = [self.sensor.moisture_read() for _ in range(15)]
        self.moisture_value = int((sum(moisture_list) / len(moisture_list)) / 10)
        self.temperature = int(((self.sensor.get_temp() * 9) / 5) + 32)
    
    def run_sensor_server(self):
        try:
            self.connect_wifi_radio()
            self.initiate_udp_server()
            wifi_refresh_timer_start = time.monotonic()
            while True:
                if wifi.radio.connected and (time.monotonic() - wifi_refresh_timer_start) < 18_000_000:
                    try:
                        buffer = bytearray(1024)
                        data, addr = self.sock.recvfrom_into(buffer)
                        decoded_request = buffer[:data].decode()
                        
                        if decoded_request == 'request_data':
                            response = f"{self.moisture_value},{self.temperature}"
                            self.sock.sendto(response.encode(), addr)
                            # ~120ms to calculate new sensor values
                            self.generate_new_sensor_values()
                            continue
                        
                        if decoded_request == 'reset':
                            wifi.radio.enabled = False
                        
                    except Exception as e:
                        print(f"Data Send/Recieve Error: {e}")
                        self.reset_sensor()
                
                self.reset_wifi_radio()
                self.initiate_udp_server()
                wifi_refresh_timer_start = time.monotonic()
                
        except Exception as e:
            print(f"WiFi Connection Error: {e}")  # Print the specific exception
            self.reset_sensor()
            
ssid = os.getenv('CIRCUITPY_WIFI_SSID')
ssid_password = os.getenv('CIRCUITPY_WIFI_PASSWORD')
i2c_address = os.getenv("I2C_ADDRESS")
i2c_bus = busio.I2C(scl=board.GP1, sda=board.GP0)
UDP_PORT = 5000

sensor_controller = SensorController(ssid=ssid, ssid_password=ssid_password, i2c_address=i2c_address, i2c_bus=i2c_bus, udp_port=UDP_PORT)
sensor_controller.run_sensor_server()