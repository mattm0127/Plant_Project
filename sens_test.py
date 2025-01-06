import time

import board

from adafruit_seesaw.seesaw import Seesaw

i2c_bus = board.I2C()
ss = Seesaw(i2c_bus, addr=0x36)

while True:
    m_read = ss.moisture_read()
    t_read = ss.get_temp()
    print(f"Moisture: {m_read}, Temp: {t_read}")
    time.sleep(.5)