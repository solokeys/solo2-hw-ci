from datetime import datetime, timedelta
import ipaddress
import six
import random
import os

from cryptography import x509
from cryptography.x509.oid import NameOID, ObjectIdentifier
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey
import asn1


# Patch out the check in CertificateBuilder that only keys that can
# sign a CRL are allowed as public keys.
#
# We could also explicitly add X25519PublicKey and X448PublicKey.
#
# For us, we're generating a cert for the X255 "communication" key.
def public_key(self, key):
    """Sets the requestor's public key (as found in the signing request)."""
    return x509.CertificateBuilder(
        self._issuer_name,
        self._subject_name,
        key,
        self._serial_number,
        self._not_valid_before,
        self._not_valid_after,
        self._extensions,
    )

x509.CertificateBuilder.public_key = public_key

def generate_cert(ca_cert, ca_key, public_key, hostname, serial_number):
    """Generates self signed certificate for a hostname, and optional IP addresses."""
    # For some reason, x509 can't handle "TRUSTED CERTIFICATE" in pem header
    ca_cert = ca_cert.replace(b"TRUSTED ", b"")

    ca_cert = x509.load_pem_x509_certificate(
        ca_cert, default_backend()
    )
    ca_key = serialization.load_pem_private_key(
        ca_key,
        password=None
    )


    name = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, hostname)
    ])
    if isinstance(public_key, X25519PublicKey):
        basic_contraints = x509.BasicConstraints(ca=False, path_length=None)
    else:
        basic_contraints = x509.BasicConstraints(ca=True, path_length=0)
    now = datetime.utcnow()

    encoder = asn1.Encoder()
    encoder.start()
    encoder.write(serial_number, asn1.Numbers.Integer)
    serial_number_der = encoder.output()

    print(public_key)

    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(ca_cert.subject)
        .public_key(public_key)
        .serial_number(serial_number)
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=50*365))
        .add_extension(basic_contraints, True)
        # Add custom extension for device serial number
        .add_extension(x509.UnrecognizedExtension(ObjectIdentifier("1.3.6.1.4.1.41482.3.7"), serial_number_der), False)
        .sign(ca_key, hashes.SHA256(), default_backend())
    )
    cert_der = cert.public_bytes(encoding=serialization.Encoding.DER)

    return cert_der

if __name__ == "__main__":
    # Usage example
    import sys
    import binascii
    import struct
    if len(sys.argv) not in [3,5]:
        print(f'usage: {sys.argv[0]} <ca_cert.pem> <ca_private_key.pem> [<output-p256-cert.der outputed255-cert.der>]')

    # generate some key pair to generate a cert for
    private_p256 = ec.generate_private_key(
        ec.SECP256R1,
        backend=None
    )
    public_p256 = private_p256.public_key()

    private_ed255 = Ed25519PrivateKey.generate()
    public_ed255 = private_ed255.public_key()

    serial_number = "11223344556677889900aabbccddeeff"
    serial_number = int.from_bytes(binascii.unhexlify(serial_number), byteorder='big', signed=False)

    ca_cert = open(sys.argv[1],'rb').read()
    ca_key  = open(sys.argv[2],'rb').read()

    cert_p256 = generate_cert(ca_cert, ca_key, public_p256, "SoloKeys PIV Attestation", serial_number=serial_number)

    cert_ed255 = generate_cert(ca_cert, ca_key, public_ed255, "SoloKeys PIV Attestation", serial_number=serial_number)

    if len(sys.argv) > 3:
        open(sys.argv[3],'wb+').write(cert_p256)
        open(sys.argv[4],'wb+').write(cert_ed255)
    else:
        print("P256:", cert_p256)
        print("Ed25519:", cert_p256)


