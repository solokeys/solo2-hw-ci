# Generates test CA and intermediate keypairs/certs for PIV attestation
# No hsm or security key integration
# This is not intended to be used for secure devices, but rather just testing/demo/hacker devices.
set -e

country=CH
state=
organization="Hacker Root Trussed CA"
unit="Demo Root CA"
CN=solokeys.com

# generate EC private key
echo "Generating root key.."
openssl genrsa -out test-root-key.pem 2048

# generate a "signing request"
echo "Generating root certifcate.."
openssl req -new -key test-root-key.pem -out test-root-key.pem.csr  -subj "/C=$country/ST=$state/O=$organization/OU=$unit/CN=$CN"

# self sign the request
openssl x509 -trustout -req -days 18250  -in test-root-key.pem.csr -signkey test-root-key.pem -out test-root-cert.pem -sha256

echo "Print cert to check"
openssl x509 -in test-root-cert.pem -text -noout

echo "Test signature with certificate.."
echo "sig test xxx" > data.txt
openssl dgst -sha256 -sign test-root-key.pem -out data.sig data.txt
openssl x509 -pubkey -noout -in test-root-cert.pem > pubkey.pem
openssl dgst -sha256 -verify pubkey.pem -signature data.sig data.txt

(($? != 0)) && { printf '%s\n' "Need to check why signature isn't working"; exit 1; }

rm -f data.txt pubkey.pem data.sig test-root-key.pem.csr

echo "Generated root cert and key."

