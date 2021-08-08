import time
import sys
import binascii
from collections import OrderedDict

import pigpio

from smartcard.System import readers
from smartcard.CardConnection import CardConnection
from smartcard.pcsc.PCSCPart10 import (SCARD_SHARE_DIRECT)

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

def set_all_gpio_to_input(pi):
    for pin in (2, 6,12,13,19,16,26,20,21):
        pi.set_mode(pin, pigpio.INPUT)
        
    # Set buttons to HIGH default when they are next set to output.
    # HIGH is read as idle button for device.
    pi.write(Pins.Button1, 1)
    pi.write(Pins.Button2, 1)
    pi.write(Pins.Button3, 1)

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

class Apdu:
    def __init__(self, cla, ins, p1, p2, data = []):
        self.header = [cla,ins,p1,p2]
        self.data = data
    
    def build(self,) -> list:
        return (self.header + [len(self.data)] + self.data)

    def __repr__(self,):
        return '<< ' + binascii.hexlify(bytes(self.build())).decode('utf8')

class ApduResponse:
    def __init__(self, data, sw1, sw2):
        self.data =data
        self.status = (sw1 << 8) | sw2

    def __repr__(self):
        return '>> ' + binascii.hexlify(bytes(self.data)).decode('utf8') + (' %02x' % (self.status))

class Reader:
    def __init__(self, reader, debug = False):
        self.reader = reader
        self.debug = debug

    @staticmethod
    def get_acr_reader():
        rlist = readers()

        for r in rlist:
            # print(r)
            # print('PICC' in r.name)

            if 'PICC' in r.name:
                reader = Reader(r)
                return reader
        return None

    def connect(self, ):
        self.conn = self.reader.createConnection()
        # self.conn.connect()
        self.conn.connect(
            # Allows connecting to reader without a card detected
            CardConnection.RAW_protocol,
            mode=SCARD_SHARE_DIRECT,
        )

    def sendRecv(self, apdu: Apdu) -> ApduResponse:
        if self.debug: print (apdu)
        data, sw1, sw2 = self.conn.transmit(
            apdu.build()
        )
        r = ApduResponse(data, sw1, sw2)
        if self.debug: print(r)
        return r



class Tester:
    def __init__(self, reader):
        self.reader = reader
        self.tlv = AcrTlv()

    def connect(self,):
        self.reader.connect()

    def start_transparent_session(self):
        # Start transparent session
        print('startSession')
        cmd = Apdu(0xff, 0xc2, 0x00, 0x00, self.tlv.build('startSession') )
        res = self.reader.sendRecv(cmd)
        print(res)

    def turn_on_field(self):
        # Turn on the field
        print('rfOn')
        cmd = Apdu(0xff, 0xc2, 0x00, 0x00, self.tlv.build('rfOn') )
        res = self.reader.sendRecv(cmd)
        print(res)

    def turn_off_field(self):
        # Turn on the field
        print('rfOff')
        cmd = Apdu(0xff, 0xc2, 0x00, 0x00, self.tlv.build('rfOff') )
        res = self.reader.sendRecv(cmd)
        print(res)

    def end_transparent_session(self,):
        # End transparent session
        cmd = Apdu(0xff, 0xc2, 0x00, 0x00, self.tlv.build('endSession') )
        res = self.reader.sendRecv(cmd)
        print(res)

def set_buttons_to_input(pi):
    # This is necessary or setting buttons to 3v3 will actually power the device by itself..
    pi.set_mode(Pins.Button1, pigpio.INPUT)
    pi.set_mode(Pins.Button2, pigpio.INPUT)
    pi.set_mode(Pins.Button3, pigpio.INPUT)

def set_buttons_to_output(pi):
    pi.set_mode(Pins.Button1, pigpio.OUTPUT)
    pi.set_mode(Pins.Button2, pigpio.OUTPUT)
    pi.set_mode(Pins.Button3, pigpio.OUTPUT)

def try_to_set_nfc_field(enable):
    # Turns on or off nfc reader if connected, skips if not.
    reader = Reader.get_acr_reader()
    if reader is not None:
        reader.connect()
        tester = Tester(reader)
        tester.start_transparent_session()
        if enable:
            tester.turn_on_field()
            tester.end_transparent_session()
        else:
            tester.turn_off_field()
            # leave transparent session on, keeping the field off..

class AcrTlv:
    def __init__(self,):
        self.config = {
            0x81: {'type': 'bytes', 'name': 'startSession'},
            0x82: {'type': 'bytes', 'name': 'endSession'},
            0x83: {'type': 'bytes', 'name': 'rfOff'},
            0x84: {'type': 'bytes', 'name': 'rfOn'},
            0x8f: {'type': 'bytes', 'name': 'switchProtocol'},
            0x90: {'type': 'bytes', 'name': 'transmitRecvFlag'},
            0x95: {'type': 'bytes', 'name': 'sendRecv'},

            0x92: {'type': 'bytes', 'name': 'bitFraming'},
            0x93: {'type': 'bytes', 'name': 'transmit'},
            0x94: {'type': 'bytes', 'name': 'recv'},

            0xff6e: {'type': 'TLV', 'name': 'setParameter'},
            0x01: {'type': 'int', 'name': 'frameSizeIFD'},
            0x02: {'type': 'int', 'name': 'frameSizeICC'},
            0x03: {'type': 'int', 'name': 'FWTI'},
            0x04: {'type': 'bytes', 'name': 'maxCommSpeedIFD'},
            0x05: {'type': 'bytes', 'name': 'maxCommSpeedICC'},
            0x06: {'type': 'bytes', 'name': 'ModulationIndex'},
            0x07: {'type': 'bytes', 'name': 'PCB'},
            0x08: {'type': 'bytes', 'name': 'CID'},
            # 0x04: {'type': 'bytes', 'name': 'maxCommSpeed'},
            # 0x05: {'type': 'bytes', 'name': 'commSpeed'},
            0x5f46: {'type': 'bytes', 'name': 'timer'},
            0x5f51: {'type': 'bytes', 'name': 'ATR'},

            0xc0: {'type': 'bytes', 'name': 'Status'},
            0x96: {'type': 'bytes', 'name': 'responseStatus'},
            0x97: {'type': 'bytes', 'name': 'cardResponse'},
        }

        # print(['%02x' % k for k in self.config.keys()])
        self.tlv = TLV(['%02x' % k for k in self.config.keys()])
    
    def parse(self, apdu: Apdu):
        p = self.tlv.parse(binascii.hexlify(bytes(apdu.data)).decode('utf8'))
        return p
    
    def print_tlv(self, apdu):
        p = self.parse(apdu)
        for key in p:
            name = self.config[int(key,16)]['name']
            print(f'{name}:', p[key])

    def build(self,tag,data = []):
        if isinstance(tag,str):
            for t in self.config:
                if self.config[t]['name'] == tag:
                    tag = t
        if isinstance(data, int):
            data = [data]
        if tag > 255:
            tag = '%04x'%tag
        else:
            tag = '%02x'%tag
        

        # res = self.tlv.build(
            # {tag : binascii.hexlify(bytes(data)).decode('utf8')}
        # )
        res = tag + ('%02x' % len(data)) + binascii.hexlify(bytes(data)).decode('utf8')

        # print('res',res)
        return list(binascii.unhexlify(res))
        
class TLV:

    def __init__(self, tags):
        self.tags = {}

        if type(tags) == list:
            for tag in tags:
                self.tags[tag] = tag
        elif type(tags) == dict:
            self.tags = tags
        else:
            print('Invalid tags dictionary given - use list of tags or dict as {tag: tag_name}')

        self.tlv_string = ''
        
        self.tag_lengths = set()
        for tag, tag_name in self.tags.items():
            self.tag_lengths.add(len(tag))


    def parse(self, tlv_string):
        """
        """
        parsed_data = OrderedDict()
        self.tlv_string = tlv_string

        i = 0
        while i < len(self.tlv_string): 
            tag_found = False

            for tag_length in self.tag_lengths:
                for tag, tag_name in self.tags.items():
                    if self.tlv_string[i:i+tag_length] == tag:
                        try:
                            value_length = int(self.tlv_string[i+tag_length:i+tag_length+2], 16)
                        except ValueError:
                            raise ValueError('Parse error: tag ' + tag + ' has incorrect data length')

                        value_start_position = i+tag_length+2
                        value_end_position = i+tag_length+2+value_length*2

                        if value_end_position > len(self.tlv_string):
                            raise ValueError('Parse error: tag ' + tag + ' declared data of length ' + str(value_length) + ', but actual data length is ' + str(int(len(self.tlv_string[value_start_position-1:-1])/2)))

                        value = self.tlv_string[value_start_position:value_end_position]
                        parsed_data[tag] = value

                        i = value_end_position
                        tag_found = True

            if not tag_found:
                msg = 'Unknown tag found: ' + binascii.hexlify(bytes(self.tlv_string[i:i+10])).decode('utf8')
                raise ValueError(msg)
        return parsed_data


    def build(self, data_dict):
        """
        """
        self.tlv_string = ''
        for tag, value in data_dict.items():
            if not value:
                return self.tlv_string

            if divmod(len(value), 2)[1] == 1:
                raise ValueError('Invalid value length - the length must be even')

            self.tlv_string = self.tlv_string + tag.upper() + hexify(len(value) / 2) + value.upper()

        return self.tlv_string


    def _parse_tvr(self, tvr, left_indent='', desc_column_width=48):
        """
        Parse terminal verification results
        """
        tvr_dump = ''

        tvr_bit_names = {
            1: ['RFU', 'SDA was selected', 'CDA failed', 'DDA failed', 'Card number appears on hotlist', 'ICC data missing', 'SDA failed', 'Offline data processing was not performed'],
            2: ['RFU', 'RFU', 'RFU', 'New card', 'Requested service not allowed for card product', 'Application not yet effective', 'Expired application', 'Card and terminal have different application versions'],
            3: ['RFU', 'RFU', 'On-line PIN entered', 'PIN entry required, PIN pad present, but PIN was not entered', 'PIN entry required, but no PIN pad present or not working', 'PIN try limit exceeded', '    Unrecognised CVM', 'Cardholder verification was not successful'],
            4: ['RFU', 'RFU', 'RFU', 'Merchant forced transaction on-line', 'Transaction selected randomly of on-line processing', 'Upper consecutive offline limit exceeded', 'Lower consecutive offline limit exceeded', 'Transaction exceeds floor limit'],
            5: ['RFU', 'RFU', 'RFU', 'RFU', 'Script processing failed after final Generate AC', 'Script processing failed before final Generate AC', 'Issuer authentication failed', 'Default TDOL Used']
        }

        for byte in range(1, 6):
            byte_value = int(tvr[byte*2-2:byte*2], 16)
            if byte_value > 0:
                byte_value_binary = '{0:b}'.format(byte_value).rjust(8, '0')
                tvr_dump = tvr_dump + '\n' + left_indent + 'Byte {}: [{}]\n'.format(byte, byte_value_binary)
                
                for j in range(0, 8):
                    if (byte_value >> j & 1) == 1:
                        tvr_dump = tvr_dump + left_indent + tvr_bit_names[byte][j][:desc_column_width].rjust(desc_column_width, ' ') + ': [1]\n'

        return tvr_dump


    def dump(self, data_dict, left_indent='', desc_column_width=48):
        """
        Trace the parsed data from tags_dict
        """
        dump = ''
        for tag, value in data_dict.items():
            dump = dump + left_indent + '[' + tag.upper().rjust(4, ' ') + '] [' + self.tags[tag.upper()][:desc_column_width].rjust(desc_column_width, ' ') + ']:[' + value + ']\n'
            # Special tag processing:
            # TVR
            if tag == '95':
                tvr_indent = left_indent + '     '
                parsed_tvr = self._parse_tvr(value, left_indent=tvr_indent, desc_column_width=48)
                if parsed_tvr:
                    dump = dump + tvr_indent + '======================== TVR ========================\n' + parsed_tvr + tvr_indent + '=====================================================\n'

        return dump



if __name__ == "__main__":
    # if running on PC, set PIGPIO_ADDR=192.168.1.111, or to whatever your pi addr is.
    pi = pigpio.pi()

    if len(sys.argv) < 2:
        print(f"usage: {sys.argv[0]} <command>")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == 'reset-pins':
        set_all_gpio_to_input(pi)

    elif command == 'reboot':
        # Toggle power
        set_all_gpio_to_input(pi)
        try_to_set_nfc_field(0)
        set_buttons_to_input(pi)
        pi.set_mode(Pins.Power, pigpio.OUTPUT)
        pi.write(Pins.Power, 0)
        time.sleep(.150)
        pi.write(Pins.Power, 1)
        set_buttons_to_output(pi)
        try_to_set_nfc_field(1)
    elif command == 'off':
        set_all_gpio_to_input(pi)
        try_to_set_nfc_field(0)
        set_buttons_to_input(pi)
        pi.set_mode(Pins.Power, pigpio.OUTPUT)
        pi.write(Pins.Power, 0)
    elif command == 'on':
        pi.set_mode(Pins.Power, pigpio.OUTPUT)
        pi.write(Pins.Power, 1)
        try_to_set_nfc_field(1)
    elif command == 'reset':
        pi.set_mode(Pins.nReset, pigpio.OUTPUT)
        pi.write(Pins.nReset, 0)
        time.sleep(.050)
        pi.set_mode(Pins.nReset, pigpio.OUTPUT)
        pi.write(Pins.nReset, 1)

    elif command == 'reboot-into-bootrom':
        set_all_gpio_to_input(pi)
        try_to_set_nfc_field(0)
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
        try_to_set_nfc_field(1)

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

    elif command == 'nfc-on':
        try_to_set_nfc_field(1)
    elif command == 'nfc-off':
        try_to_set_nfc_field(0)
    elif command == 'switch-into-passive-mode':
        set_all_gpio_to_input(pi)
        try_to_set_nfc_field(0)
        set_buttons_to_input(pi)
        pi.set_mode(Pins.Power, pigpio.OUTPUT)
        pi.set_mode(Pins.ISP, pigpio.OUTPUT)
        pi.write(Pins.Power, 0)
        time.sleep(.250)

        try_to_set_nfc_field(1)
    else:
        raise ValueError(f"Invalid command: {command}")



def hexify(number):
    """
    Convert integer to hex string representation, e.g. 12 to '0C'
    """
    if number < 0:
        raise ValueError('Invalid number to hexify - must be positive')

    result = hex(int(number)).replace('0x', '').upper()
    if divmod(len(result), 2)[1] == 1:
        # Padding
        result = '0{}'.format(result)
    return result

