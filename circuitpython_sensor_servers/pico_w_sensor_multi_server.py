import storage
import os
import wifi
import socketpool
import board
import busio
import time
import microcontroller
import toml

from adafruit_httpserver import Server, Response, Request
from adafruit_seesaw.seesaw import Seesaw

class AP_HTTPServer:

    AP_SSID = 'Pico Moisture Sensor'
    AP_PASSWORD = 'connect123'
    AP_PORT = 5000

    def __init__(self):
        self.pool = socketpool.SocketPool(wifi.radio)
        self.server = Server(self.pool)
        self.ap_host_ip = None

    def initiate_ap_radio(self):
        print("Initiating Access Point...")
        wifi.radio.start_ap(ssid=self.AP_SSID, password=self.AP_PASSWORD)
        self.ap_host_ip = str(wifi.radio.ipv4_address_ap)
        if wifi.radio.ap_active:
            print(f"Access Point Online, {self.AP_SSID}")
    
    def deactivate_ap_radio(self):
        print("Deactivating Access Point...")
        wifi.radio.stop_ap()
        print("Access Point Offline.")

    def initiate_HTTP_server(self):
        print("Initiating HTTP Server...")
        self.server.start(host=self.ap_host_ip, port=self.AP_PORT)
        print(f"HTTP Server Online: IP:{self.server.host}, Port:{self.server.port}")
    
    def deactivate_HTTP_server(self):
        print("Deactivating HTTP Server...")
        self.server.stop()
        print("HTTP Server Offline")
    
    def save_client_response(self, client_settings):
        storage.remount("/", False)
        with open("/settings.toml", "w") as save_file:
            toml.dump(client_settings, save_file)
            print("Settings Saved")
        with open("/settings.toml", "r") as settings_file:
            contents = settings_file.read()
        contents = contents.replace("'", '"')
        with open("/settings.toml", "w") as settings_file:
            settings_file.write(contents)
            print("Settings Formatted")
        self.deactivate_ap_radio()
        self.deactivate_HTTP_server()

class SensorController:
    
    def __init__(self, ssid, ssid_password, i2c_address, i2c_bus, udp_port):
        self.sensor = Seesaw(i2c_bus, i2c_address)
        self.ssid = ssid
        self.ssid_password = ssid_password
        self.udp_host = None
        self.udp_port = udp_port
        self.pool = socketpool.SocketPool(wifi.radio)
        self.sock = None
        self.moisture_value = int(self.sensor.moisture_read() / 10)
        self.temperature = int(((self.sensor.get_temp() * 9) / 5) + 32)

    def connect_wifi_radio(self):
        # Connect to Wi-Fi
        print("Connecting to Wifi...")
        wifi.radio.connect(self.ssid, self.ssid_password)
        self.udp_host = str(wifi.radio.ipv4_address)
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
                if wifi.radio.connected and (time.monotonic() - wifi_refresh_timer_start) < 1800:
                    try:
                        buffer = bytearray(1024)
                        data, addr = self.sock.recvfrom_into(buffer)
                        decoded_request = buffer[:data].decode()

                        if decoded_request.endswith('request_data'):
                            request_id = decoded_request.split(':')[0]
                            #print(f"Recieved: {request_id}")
                            response = f"{request_id}:{self.moisture_value},{self.temperature}"
                            self.sock.sendto(response.encode(), addr)
                            #print(f"Sent : {request_id}")
                            # ~120ms to calculate new sensor values
                            self.generate_new_sensor_values()
                            continue

                        if decoded_request == 'reset':
                            print(f"Request:{request_id}: WiFi Reset Reset Recieved")
                            wifi.radio.enabled = False

                    except Exception as e:
                        print(f"Data Send/Recieve Error(Request:{request_id}): {e}")
                        wifi.radio.enabled = False

                self.reset_wifi_radio()
                self.initiate_udp_server()
                wifi_refresh_timer_start = time.monotonic()

        except Exception as e:
            print(f"WiFi Connection Error: {e}")  # Print the specific exception
            self.reset_wifi_radio()
            self.initiate_udp_server()
            wifi_refresh_timer_start = time.monotonic()

# ----- Main Controller Operation ----- 

if not os.getenv('CIRCUITPY_WIFI_SSID'):
    ap_http_server = AP_HTTPServer()
    ap_http_server.initiate_ap_radio()
    ap_http_server.initiate_HTTP_server()
    
    @ap_http_server.server.route("/credentials", "POST")
    def credential_handler(Request):
        form_data = Request.form_data
        if form_data is not None:
            try:
                form_ssid = form_data["SSID"].replace("+", " ")
                form_password = form_data["SSID_PASSWORD"]
                wifi.radio.connect(form_ssid, form_password)
                if wifi.radio.connected:
                    global received_data
                    received_data = {"CIRCUITPY_WIFI_SSID": str(form_ssid), "CIRCUITPY_WIFI_PASSWORD": str(form_password)}
            except:
                return Response(Request, "WiFi Credentials Inncorrect", status=400) 
                
            return Response(Request, body=f"{wifi.radio.ipv4_address}", content_type='text/plain')
        else:
            return Response(Request, "No form data received", status=400) 
            
    received_data = None
    while received_data is None:
        ap_http_server.server.poll()
    
    print(f"Network: {received_data['CIRCUITPY_WIFI_SSID']} connected, restarting...")
    time.sleep(1)
    ap_http_server.save_client_response(client_settings=received_data)
    microcontroller.reset()

ssid = os.getenv('CIRCUITPY_WIFI_SSID')
ssid_password = os.getenv('CIRCUITPY_WIFI_PASSWORD')
i2c_address = 0x36
i2c_bus = busio.I2C(scl=board.GP1, sda=board.GP0)
UDP_PORT = 5000

sensor_controller = SensorController(ssid=ssid, ssid_password=ssid_password, i2c_address=i2c_address, i2c_bus=i2c_bus, udp_port=UDP_PORT)
sensor_controller.run_sensor_server()
