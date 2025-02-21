# WaterMe Lite

A project that displays a fun, interactive screen showing the moisture and temperature of your houseplant's soil, using a Raspberry Pi Pico W for sensing and a separate display for visualization.

## Screenshot
![Screenshot 2025-01-13 172937](https://github.com/user-attachments/assets/d0c9f5ff-3daa-4794-b935-c31423e68c00)

![Screenshot 2025-01-13 173112](https://github.com/user-attachments/assets/017bc9ba-044b-472f-a5f9-d4ef89bc8087)

## Features

* Reads moisture and temperature data from a sensor connected to a Raspberry Pi Pico W.
* Communicates with the Pico W over UDP.
* Displays the data on a full screen UI with animated eyes and dynamic messages.
* Provides a fun and engaging way to monitor your plant's health.

## Project Structure

This project consists of two main files:

* **`water_me_pi_lite_pico.py`:** This file runs on a device with a display (e.g., a Raspberry Pi) and is responsible for the visual elements of the project, receiving data from the Pico W, and displaying it in an engaging way.
* **`pico_w_sensor_multi_server.py`:** This file runs on the Raspberry Pi Pico W and handles the following:
    *  Reading data from the soil moisture and temperature sensor.
    *  Creating a UDP server to send data to the display device.
    *  Creating an Access Point for initial WiFi configuration.
    *  Connecting to WiFi based on provided credentials.

## Hardware Requirements

* Raspberry Pi Pico W
* Soil moisture and temperature sensor (compatible with the Pico W, such as the Adafruit STEMMA Soil Sensor)
* Display device (e.g., a Raspberry Pi with HDMI Display)

## Software Requirements

* **For the display device (e.g., Raspberry Pi):**
    * Python 3.7 or higher
    * Pygame library
* **For the Raspberry Pi Pico W:**
    * MicroPython firmware
    * Adafruit CircuitPython libraries:
        * `adafruit_httpserver`
        * `adafruit_datetime`
        * `adafruit_seesaw`

## Installation

**1. Pico W Setup:**

   * Install MicroPython on the Pico W.
   * Install the required Adafruit libraries using `circup` or manually.
   * Copy the `pico_w_sensor_multi_server.py` file to the Pico W.

**2. Display Device Setup:**

   * Install Python 3.7 or higher.
   * Install the Pygame library using `pip install pygame`.
   * Copy the `water_me_pi_lite_pico.py` file to the display device.
   * Change pico_udp_ip_address in __name__==__main__ to your sensor devices ip
   IN DEVELOPMENT
   * Pico W sends ip information once connected to wifi network from AP

**3. WiFi Configuration:**
   * In the Pico W settings.toml file, add CIRCUITPY_WIFI_SSID and CIRCUITPY_WIFI_PASSWORD and set them to your wifi and password
   IN DEVELOPMENT
   * Power on the Pico W. It will create a WiFi access point named "Pico Moisture Sensor".
   * Connect to this access point from your computer or mobile device.
   * Open a web browser and navigate to the IP address shown in the serial output of the Pico W (usually `192.168.4.1`).
   * Enter your home WiFi SSID and password on the webpage to configure the Pico W.
   * The Pico W will reset and connect to your home WiFi.
## Usage

1. Run the `water_me_pi_lite_pico.py` file on the display device.
2. The display will show the moisture and temperature readings from the sensor connected to the Pico W.
3. The animated eyes will blink and look around, and the messages will change dynamically based on the sensor readings.

## Flow Diagram
![Screenshot 2025-02-20 213053](https://github.com/user-attachments/assets/2766879a-ab33-49d3-91e9-d25820dd95b2)


## Contributing

Contributions are welcome! Please feel free to submit pull requests or issues.

## License

This project is licensed under the MIT License.

## Acknowledgements

This project was inspired by the WaterMe project by [original creator's name].
