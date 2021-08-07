import time
import sys

import pigpio

# pi pin | cable color  | pi function   | solo pin
# -----------------------------------------
# 3        any/extra       GPIO2          (connected to external power circuit..)
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
    Power = 2

    # Map solo function to Rpi GPIO #
    Button1 = 12
    Button2 = 6
    Button3 = 26

    ExtraGpio1 = 19
    ExtraGpio2 = 16

    nReset = 21
    ISP = 13

if __name__ == "__main__":
    # if running on PC, set PIGPIO_ADDR=192.168.1.111, or to whatever your pi addr is.
    pi = pigpio.pi()

    if len(sys.argv) < 2:
        print(f"usage: {sys.argv[0]} <command>")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == 'reboot':
        # Toggle power
        pi.set_mode(Pins.Power, pigpio.OUTPUT)
        pi.write(Pins.Power, 0)
        time.sleep(.150)
        pi.write(Pins.Power, 1)
    elif command == 'off':
        pi.set_mode(Pins.Power, pigpio.OUTPUT)
        pi.write(Pins.Power, 0)
    elif command == 'on':
        pi.set_mode(Pins.Power, pigpio.OUTPUT)
        pi.write(Pins.Power, 1)
    elif command == 'reset':
        pi.set_mode(Pins.nReset, pigpio.OUTPUT)
        pi.write(Pins.nReset, 0)
        time.sleep(.050)
        pi.set_mode(Pins.nReset, pigpio.OUTPUT)
        pi.write(Pins.nReset, 1)

    elif command == 'reboot-into-bootrom':
        pi.set_mode(Pins.Power, pigpio.OUTPUT)
        pi.set_mode(Pins.ISP, pigpio.OUTPUT)
        pi.write(Pins.Power, 0)

        # while power is turned out, assert ISP.
        pi.write(Pins.ISP, 0)
        time.sleep(.050)
        pi.write(Pins.Power, 1)

        # after 50ms release ISP
        time.sleep(.050)
        pi.write(Pins.ISP, 1)

    elif command == 'reset-into-bootrom':
        pi.set_mode(Pins.nReset, pigpio.OUTPUT)
        pi.set_mode(Pins.ISP, pigpio.OUTPUT)
        pi.write(Pins.nReset, 0)

        # while reset asserted, assert ISP.
        pi.write(Pins.ISP, 0)
        time.sleep(.050)
        pi.write(Pins.nReset, 1)

        # after 50ms release nReset
        time.sleep(.050)
        pi.write(Pins.ISP, 1)

    else:
        raise ValueError(f"Invalid command: {command}")