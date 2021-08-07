import sys
import os
import binascii
import random
import time

from cbor2 import dumps, loads

from util import Constants, SmartCardDevice, assert_ok, select, reset_fs, assert_not_ok, SmartCardError
from cert_gen import generate_cert
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric import ed25519


def write_random_file(card):
    while True:
        tester_filename_id = b'\xe1\x01'
        tester_file_id = b'\xe1\x02'

        fn_len = random.randint(6,12)
        file_len = random.randint(16, 2048)
        filename = binascii.hexlify(os.urandom(fn_len))

        contents = os.urandom(file_len)

        print('writing contents to', filename)
        print(contents[:64])

        # Select filename buffer
        res = card.transmit_recv(0x00, Constants.Ins.Select, 0x00, 0x00, tester_filename_id)
        assert_ok(res)

        # Write filename
        res = card.transmit_recv(0x00, Constants.Ins.WriteBinary, 0x00, 0x00, filename)
        assert_ok(res)

        # Select file buffer
        res = card.transmit_recv(0x00, Constants.Ins.Select, 0x00, 0x00, tester_file_id)
        assert_ok(res)

        # Write file contents
        res = card.transmit_recv(0x00, Constants.Ins.WriteBinary, 0x00, 0x00, contents)
        assert_ok(res)

        # flush
        res = card.transmit_recv(0x00, Constants.Ins.WriteFile, 0x00, 0x00)
        assert_ok(res)
        yield (fn_len, file_len)

def get_uuid(card,):
    # flush
    res = card.transmit_recv(0x00, Constants.Ins.GetUUID, 0x00, 0x00)
    assert_ok(res)

    assert len(res[:-2]) == 16
    return res[:-2]

if __name__ == "__main__":
    if len(sys.argv) != 1:
        print('Usage: %s ' % sys.argv[0])
        sys.exit(1)


    card = next(SmartCardDevice.list_devices())


    print ("Selecting tester..")
    select(card)

    print("Writing random files..")
    fn_sum = 0
    file_sum = 0
    count = 0
    for i in range(0,10* 1000):
        try:
            select(card)
            get_uuid(card)
            (fn, f) = next(write_random_file(card,))
            fn_sum += fn
            file_sum += f
            count += 1
            print(i)
        except SmartCardError as e:
            if e.code == 0x6a82:
                # Thanks PCSC..
                pass
            elif e.code == 0x6a84:
                # not enough memory
                print()
                print(f"reset on {fn_sum}, {file_sum}.  {count} files")
                print()
                time.sleep(1)
                select(card)
                res = card.transmit_recv(0x00, Constants.Ins.ReformatFs, 0x00, 0x00)
                assert_ok(res)
                fn_sum = 0
                file_sum = 0
                count = 0
                sys.exit(1)