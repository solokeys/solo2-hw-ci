import time

import pigpio

# pi pin | cable color  | pi function   | solo pin
# -----------------------------------------
# 3        any/extra       GPIO2
# ...
# 31     | black        | GPIO6        | Button2
# 32     | white        | GPIO12       | Button1
# 33     | grey         | GPIO13       | ISP
# 34     | purple       | GND          | GND
# 35     | blue         | GPIO19       | ExtraGpio1
# 36     | green        | GPIO16       | ExtraGpio2
# 37     | yellow       | GPIO26       | Button3
# 38     | orange       | GPIO20       | 3v3
# 39     | red          | GND          | GND
# 40     | brown        | GPIO21       | nRESET
# 

class Pins:
    # Map solo function to Rpi GPIO #
    Button1 = 12
    Button2 = 6
    Button3 = 26

    ExtraGpio1 = 19
    ExtraGpio2 = 16

if __name__ == "__main__":
    # if running on PC, set PIGPIO_ADDR=192.168.1.111, or to whatever your pi addr is.
    pi = pigpio.pi()

    print('running gpio on pi')

    pi.set_mode(Pins.ExtraGpio1, pigpio.OUTPUT)
    pi.set_mode(Pins.ExtraGpio2, pigpio.OUTPUT)


    pi.write(Pins.ExtraGpio1, 0)
    pi.write(Pins.ExtraGpio2, 1)
    print('1')
    time.sleep(1)

    pi.write(Pins.ExtraGpio1, 1)
    pi.write(Pins.ExtraGpio2, 0)

    print('2')
    time.sleep(1)

    pi.set_mode(Pins.ExtraGpio1, pigpio.INPUT)
    pi.set_mode(Pins.ExtraGpio2, pigpio.INPUT)

