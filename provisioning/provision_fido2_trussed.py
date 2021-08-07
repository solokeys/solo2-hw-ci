import sys
import struct
import hmac
import hashlib

import ecdsa

from cbor2 import dumps, loads

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric import ed25519, x25519

from write_random import write_random_file
from util import Constants, SmartCardDevice, assert_ok, select, reset_fs, assert_not_ok, SmartCardError
from cert_gen import generate_cert


def write_file(card, filename, contents):
    tester_filename_id = b'\xe1\x01'
    tester_file_id = b'\xe1\x02'

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

def get_uuid(card,):
    # flush
    res = card.transmit_recv(0x00, Constants.Ins.GetUUID, 0x00, 0x00)
    assert_ok(res)

    assert len(res[:-2]) == 16
    return res[:-2]

def run_trussed_attestation(card,uuid,ca_cert_path,ca_key_path):

    # Test that writing certs first doesn't work
    res = card.transmit_recv(0x00, Constants.Ins.SaveP256Cert, 0x00, 0x00, b"\xAB" * 1500)
    assert_not_ok(res)
    res = card.transmit_recv(0x00, Constants.Ins.SaveED255Cert, 0x00, 0x00, b"\xAB" * 1500)
    assert_not_ok(res)

    # Generate secret key
    res = card.transmit_recv(0x00, Constants.Ins.GenerateP256, 0x00, 0x00)
    assert_ok(res)
    assert len(res[:-2]) == 64  # P256 public key should be 64 bytes
    x = int.from_bytes(res[:32], byteorder='big', signed=False)
    y = int.from_bytes(res[32:64], byteorder='big', signed=False)
    public_p256 = ec.EllipticCurvePublicNumbers(x, y, ec.SECP256R1()).public_key()

    # Generate secret key
    res = card.transmit_recv(0x00, Constants.Ins.GenerateED255, 0x00, 0x00)
    assert_ok(res)
    assert len(res[:-2]) == 32  # ED255 public key should be 32 bytes
    public_ed255 = ed25519.Ed25519PublicKey.from_public_bytes(res[:32])

    # Generate secret key
    res = card.transmit_recv(0x00, Constants.Ins.GenerateX255, 0x00, 0x00)
    assert_ok(res)
    assert len(res[:-2]) == 32  # ED255 public key should be 32 bytes
    public_x255 = x25519.X25519PublicKey.from_public_bytes(res[:32])

    uuid_integer = int.from_bytes(uuid, byteorder='big', signed=False)
    hostname = "SoloKeys trussed Attestation"
    cert_p256  = generate_cert(ca_cert, ca_key, public_p256, hostname, serial_number=uuid_integer)
    cert_ed255 = generate_cert(ca_cert, ca_key, public_ed255, hostname, serial_number=uuid_integer)
    cert_x255 = generate_cert(ca_cert, ca_key, public_x255, hostname, serial_number=uuid_integer)


    # Test that writing tiny certs doesn't work
    res = card.transmit_recv(0x00, Constants.Ins.SaveP256Cert, 0x00, 0x00, b"\xAB" * 16)
    assert_not_ok(res)
    res = card.transmit_recv(0x00, Constants.Ins.SaveED255Cert, 0x00, 0x00, b"\xAB" * 16)
    assert_not_ok(res)
    res = card.transmit_recv(0x00, Constants.Ins.SaveX255Cert, 0x00, 0x00, b"\xAB" * 16)
    assert_not_ok(res)

    # Write back certificates
    res = card.transmit_recv(0x00, Constants.Ins.SaveP256Cert, 0x00, 0x00, cert_p256)
    assert_ok(res)
    res = card.transmit_recv(0x00, Constants.Ins.SaveED255Cert, 0x00, 0x00, cert_ed255)
    assert_ok(res)
    res = card.transmit_recv(0x00, Constants.Ins.SaveX255Cert, 0x00, 0x00, cert_x255)
    assert_ok(res)

    # Write T1 public key (dont currently have ed255 cert in setup, but any random bytes will do)
    res = card.transmit_recv(0x00, Constants.Ins.SaveT1IntermediatePublicKey, 0x00, 0x00, b'A' * 32)
    assert_ok(res)


def test_trussed_attestation(card,):
    """
    If the test firmware is compiled with `--features test-attestation`, then this
    basic TestAttestation ins will be exposed.  P1 determines test function, as follows.

    0 - Return 32 byte challenge + DER signature using P256 attn key.
    1 - Return P256 attn cert
    2 - Return 32 byte challenge + DER signature using ED255 attn key.
    3 - Return ED255 attn cert
    """
    print("Testing P256...")
    res = card.transmit_recv(0x00, Constants.Ins.TestAttestation, 0x00, 0x00)
    code = res[-1] | (res[-2] << 8)
    if code == 0x6a81:
        print("TestAttestion is NOT enabled in device, skipping.")
        return
    assert_ok(res)
    chal = res[0:32]
    sig = res[32:-2]

    res = card.transmit_recv(0x00, Constants.Ins.TestAttestation, 0x01, 0x00)
    assert_ok(res)
    cert_der = res[:-2]
    cert = x509.load_der_x509_certificate(cert_der)

    cert.public_key().verify(sig, chal, ec.ECDSA(hashes.SHA256()))
    print("Testing ED255...")
    res = card.transmit_recv(0x00, Constants.Ins.TestAttestation, 0x02, 0x00)
    assert_ok(res)
    chal = res[0:32]
    sig = res[32:-2]

    res = card.transmit_recv(0x00, Constants.Ins.TestAttestation, 0x03, 0x00)
    assert_ok(res)
    cert_der = res[:-2]
    cert = x509.load_der_x509_certificate(cert_der)
    # taking more pedantic way to verify ed255 sig.
    pubkey_ed255 = ed25519.Ed25519PublicKey.from_public_bytes(
        cert.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    )

    pubkey_ed255.verify(sig, chal)
    print("Testing X255...")
    our_x255 = x25519.X25519PrivateKey.generate()
    our_x255_bytes = our_x255.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)

    res = card.transmit_recv(0x00, Constants.Ins.TestAttestation, 0x04, 0x00, our_x255_bytes)
    assert_ok(res)
    chal = res[0:32]
    sig = res[32:-2]
    print('GOT OK')

    res = card.transmit_recv(0x00, Constants.Ins.TestAttestation, 0x05, 0x00)
    assert_ok(res)
    cert_der = res[:-2]
    cert = x509.load_der_x509_certificate(cert_der)
    # taking more pedantic way to verify ed255 sig.
    pubkey_x255 = x25519.X25519PublicKey.from_public_bytes(
        cert.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    )

    shared_key = our_x255.exchange(pubkey_x255)
    our_sig = hmac.new(
        shared_key,
        msg=chal,
        digestmod=hashlib.sha256
    ).digest()
    assert our_sig == sig

    print("Attestation is valid.")



if len(sys.argv) != 5:
    print('Usage: %s <fido-attestation-cert.der> <fido-attestation-key.pem> <ca-intermediate-cert.pem> <ca-intermediate-key.pem>' % sys.argv[0])
    sys.exit(1)

cert_der = open(sys.argv[1],'rb').read()
private_key_pem = open(sys.argv[2],'rb').read()
private_key_raw = ecdsa.SigningKey.from_pem(private_key_pem).to_string()

# for trussed certs
ca_cert = open(sys.argv[3],'rb').read()
ca_key = open(sys.argv[4],'rb').read()

try:
    card = next(SmartCardDevice.list_devices(name = "Provisioner"))
except:
    card = next(SmartCardDevice.list_devices(name = "SoloKeys"))

fido2_key_filename = b'/fido/sec/00'
fido2_cert_filename = b'/fido/x5c/00'


try:

    print ("Selecting tester and resetting..")
    select(card)
    reset_fs(card)

    print("Writing FIDO2 attestation")
    flags = (1 << 1) # SENSITIVE
    kind = 5 # P256
    write_file(card, fido2_key_filename, struct.pack(">HH", flags, kind) + private_key_raw)
    write_file(card, fido2_cert_filename, cert_der)

    print("Generating trussed attestation")


    uuid = get_uuid(card)

    for i in range(0,10):
        write_random_file(card)

    run_trussed_attestation(card, uuid, ca_cert, ca_key)

    for i in range(0,10):
        write_random_file(card)

    test_trussed_attestation(card)

except SmartCardError as e:
    # Occasionally the OS's PCSC steps in and tries to select some nonexistant app,
    # making our test return "not found" because our applet is no longer selected..
    assert e.code == 0x6a82
    print("Thanks pcsc. restarting..")
