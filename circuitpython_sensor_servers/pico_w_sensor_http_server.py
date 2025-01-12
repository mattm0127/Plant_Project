import os
import wifi
import socketpool
import board
import busio
import time
from adafruit_httpserver import Server, Response, Request
from adafruit_seesaw.seesaw import Seesaw

ssid = os.getenv('CIRCUITPY_WIFI_SSID')
password = os.getenv('CIRCUITPY_WIFI_PASSWORD')
i2c_address = os.getenv("I2C_ADDRESS")
i2c_bus = busio.I2C(scl = board.GP1, sda=board.GP0)
sensor = Seesaw(i2c_bus, i2c_address)
moisture_list = []
moisture_value = 0
temperature = 0

try:
    # Connect to Wi-Fi
    print("Connecting to wifi...")
    wifi.radio.connect(ssid, password)
    print("Connected to Wi-Fi")
    print(f"My IP address is {wifi.radio.ipv4_address}")
    pico_ip = str(wifi.radio.ipv4_address)
    print("Initiating Server...")
    pool = socketpool.SocketPool(wifi.radio)
    server = Server(pool)

    @server.route("/moisture-temperature")
    def moisture_temperature_handler(Request):
        try:
            return Response(Request, body=f"{str(moisture_value)},{str(temperature)}", content_type = 'text/plain')
        except Exception as e:
            print(f"Error in moisture_handler: {e}")  # Print the error to the serial console
            return Response(Request, body="Error", status_code=500, content_type="text/plain")

    @server.route("/moisture")
    def moisture_handler(Request):
        try:
            #moisture_list = [sensor.moisture_read() for _ in range(15)]
            #moisture_value = int((sum(moisture_list) / len(moisture_list)) / 10)
            return Response(Request, body=str(moisture_value), content_type = 'text/plain')
        except Exception as e:
            print(f"Error in moisture_handler: {e}")  # Print the error to the serial console
            return Response(Request, body="Error", status_code=500, content_type="text/plain")

    @server.route("/temperature")
    def temperature_handler(Request):
        try:
            #temperature = sensor.get_temp()
            #temperature = int(((temperature * 9) / 5) + 32)
            return Response(Request, body=str(temperature), content_type = 'text/plain')
        except Exception as e:
            print(f"Error in moisture_handler: {e}")  # Print the error to the serial console
            return Response(Request, body="Error", status_code=500, content_type="text/plain")

    server.start(host=pico_ip)
    print(f"Server Created on {server.host}, listening for requests on: {server.port}")
    while True:
        server.poll()
        moisture_list = [sensor.moisture_read() for _ in range(15)]
        moisture_value = int((sum(moisture_list) / len(moisture_list)) / 10)
        temperature = int(((sensor.get_temp() * 9) / 5) + 32)
    print("WiFi Connection Closed.")

except Exception as e:
    print(f"Error: {e}")  # Print the specific exception
    time.sleep(5)
    print("Restarting...")
    import microcontroller
    microcontroller.reset()
