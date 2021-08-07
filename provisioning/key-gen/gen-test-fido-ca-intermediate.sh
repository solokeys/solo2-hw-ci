set -ex
# Generates test intermediate CA and intermediate keypairs/certs for FIDO2 attestation
# No hsm or security key integration
# This is not intended to be used for secure devices, but rather just testing/demo/hacker devices.

#Generate the intermediate
openssl ecparam -genkey -name prime256v1 -out test-intermediate-key.pem
openssl req -new -key test-intermediate-key.pem -out test-intermediate-cert.pem.csr  -subj "/C=CH/ST=/O=Hacker Intermediate/OU=Demo FIDO2 Attestation/CN=Demo FIDO2 Intermediate CA"
echo "signing intermediate with root key.."
serial="0xbbbbbbbbbbbbbbbb"
cat > v3-intermediate.ext << EOF
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid,issuer
basicConstraints=critical,CA:TRUE
keyUsage = critical, keyCertSign, cRLSign
EOF

# Sign the intermediate with root
openssl x509 -trustout -req -days 18250  -in test-intermediate-cert.pem.csr  -out test-intermediate-cert.pem -sha256 -CA ../test-root-cert.pem -CAkey ../test-root-key.pem -extfile v3-intermediate.ext -set_serial $serial
rm -f v3-intermediate.ext test-intermediate-cert.pem.csr

country=US
state=
organization=SoloKeys
unit="Authenticator Attestation"
serial="0xaaaaaaaaaaaaaaaa"
CN="Demo FIDO2 Attestation Serial $serial"
email=


openssl ecparam -genkey -name prime256v1 -out test-key.pem

echo "generating signing request"

openssl req -new -key test-key.pem -out test-key.pem.csr  -subj "/C=$country/ST=$state/O=$organization/OU=$unit/CN=$CN"

cat > v3.ext << EOF
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
# AAGUID
1.3.6.1.4.1.45724.1.1.4=ASN1:FORMAT:HEX,OCTETSTRING:8bc5496807b14d5fb249607f5d527da2
# Transports (USB, NFC)
1.3.6.1.4.1.45724.2.1.1=ASN1:FORMAT:BITLIST,BITSTRING:2,3
EOF


echo "signing certificate with intermediate.."
openssl x509 -trustout -req -days 18250  -in test-key.pem.csr  -out test-cert.pem -sha256 -CA test-intermediate-cert.pem -CAkey test-intermediate-key.pem -extfile v3.ext -set_serial $serial
rm -f v3.ext

openssl ec -in test-key.pem  -outform der -out test-key.der
openssl x509 -in test-cert.pem  -outform der -out test-cert.der
openssl x509 -in test-cert.der -inform der -text -noout

echo "Test signature.."
echo "test data to sign xxx $RANDOM" > data.txt
openssl dgst -sha256 -sign test-key.pem -out data.sig data.txt
openssl x509 -in test-cert.pem -pubkey -noout > pubkey.pem
openssl dgst -sha256 -verify pubkey.pem -signature data.sig data.txt
(($? != 0)) && { printf '%s\n' "Need to check why signature isn't working"; exit 1; }
rm -f data.txt pubkey.pem data.sig

echo "Verify chain.."
openssl verify -verbose -CAfile <(cat "../test-root-cert.pem" "test-intermediate-cert.pem") "test-cert.pem"
(($? != 0)) && { printf '%s\n' "Need to check why signature isn't working"; exit 1; }

rm -f test-key.pem.csr

echo "FIDO2 attestation key and cert $serial created & signed."
echo "root: ../test-root-key.pem ../test-root-cert.pem"
echo "intermediate: test-key.pem test-cert.der"


