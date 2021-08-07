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

def set_buttons_to_input(pi):
    # This is necessary or setting buttons to 3v3 will actually power the device by itself..
    pi.set_mode(Pins.Button1, pigpio.INPUT)
    pi.set_mode(Pins.Button2, pigpio.INPUT)
    pi.set_mode(Pins.Button3, pigpio.INPUT)

def set_buttons_to_output(pi):
    pi.set_mode(Pins.Button1, pigpio.OUTPUT)
    pi.set_mode(Pins.Button2, pigpio.OUTPUT)
    pi.set_mode(Pins.Button3, pigpio.OUTPUT)



if __name__ == "__main__":
    # if running on PC, set PIGPIO_ADDR=192.168.1.111, or to whatever your pi addr is.
    pi = pigpio.pi()

    if len(sys.argv) < 2:
        print(f"usage: {sys.argv[0]} <command>")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == 'reboot':
        # Toggle power
        set_buttons_to_input(pi)
        pi.set_mode(Pins.Power, pigpio.OUTPUT)
        pi.write(Pins.Power, 0)
        time.sleep(.150)
        pi.write(Pins.Power, 1)
        set_buttons_to_output(pi)
    elif command == 'off':
        set_buttons_to_input(pi)
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
        set_buttons_to_input(pi)
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
        set_buttons_to_output(pi)

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
    elif command == 'reset-buttons':
        pi.set_mode(Pins.Button1, pigpio.OUTPUT)
        pi.set_mode(Pins.Button2, pigpio.OUTPUT)
        pi.set_mode(Pins.Button3, pigpio.OUTPUT)

        pi.write(Pins.Button1, 1)
        pi.write(Pins.Button2, 1)
        pi.write(Pins.Button3, 1)
    elif command == 'toggle-button-1':
        pi.set_mode(Pins.Button1, pigpio.OUTPUT)
        pi.write(Pins.Button1, 0)
        time.sleep(.100)
        pi.write(Pins.Button1, 1)

    elif command == 'toggle-button-2':
        pi.set_mode(Pins.Button2, pigpio.OUTPUT)
        pi.write(Pins.Button2, 0)
        time.sleep(.100)
        pi.write(Pins.Button2, 1)

    elif command == 'toggle-button-3':
        pi.set_mode(Pins.Button3, pigpio.OUTPUT)
        pi.write(Pins.Button3, 0)
        time.sleep(.100)
        pi.write(Pins.Button3, 1)


    else:
        raise ValueError(f"Invalid command: {command}")