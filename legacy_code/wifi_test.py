import requests
import time
import socket
import threading

class SensorHTTPClient:
    """Class for getting data from the sensor."""
    BASE_URL = 'http://'
    TIMEOUT_VALUE = 0.06
    HTTP_IP = "192.168.4.1"
    HTTP_PORT = 5000

    def __init__(self):
        None
            
    def _sensor_request(self, request_type, sensor_data_request, data=''):
        url = f"{self.BASE_URL}{self.HTTP_IP}:{self.HTTP_PORT}/{sensor_data_request}"
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        if request_type.upper() == 'GET':
            try:
                response = requests.get(url, timeout=self.TIMEOUT_VALUE)
                value = response.text
                return value
            except requests.exceptions.RequestException as e:
                print(f"Error: {e}")

        if request_type.upper() == 'POST':
            try:
                response = requests.post(url=url, data=data, headers=headers)
                sensor_ip_address = response.text
                return sensor_ip_address
            except requests.exceptions.RequestException as e:
                print(f"Error: {e}")

    def send_wifi_credentials(self):
        data = {'SSID': '...They Will Come', 'SSID_PASSWORD': '55hudson1n'}
        sensor_ip_address = self._sensor_request("post", 'credentials', data=data)
        return sensor_ip_address

    def get_values(self):
        combined_values = self._sensor_request('get','moisture-temperature')
        return combined_values.split(',')
    
    def get_moisture_value(self):
        moisture_value = self._sensor_request('get', 'moisture')
        return moisture_value

    def get_temperature_value(self):
        temperature_value = self._sensor_request('get', 'temperature')
        return temperature_value

sensor = SensorHTTPClient()
ip_response = sensor.send_wifi_credentials()
print(ip_response)