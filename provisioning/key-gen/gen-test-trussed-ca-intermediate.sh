# Generates test CA and intermediate keypairs/certs for PIV attestation
# No hsm or security key integration
# This is not intended to be used for secure devices, but rather just testing/demo/hacker devices.

set -e
echo "Now generating intermediate"

country=
state=
organization=SoloKeys
unit="Demo Trussed Attestation"
serial="0xaaaaaaaaaaaaaaaa"
CN="Demo Trussed Sub CA Serial $serial"
email=



echo "generating p256 key"
openssl ecparam -genkey -name secp256r1 -out test-key-p256.pem

echo "generating signing request for p256"

openssl req -new -key test-key-p256.pem -out test-key-p256.pem.csr  -subj "/C=$country/ST=$state/O=$organization/OU=$unit/CN=$CN"

# sign the request

cat > v3.ext << EOF
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid,issuer
basicConstraints=critical,CA:true,pathlen:1
keyUsage=critical, keyCertSign
1.3.6.1.4.1.41482.3.7=ASN1:FORMAT:HEX,BITSTRING:$(echo $serial | tr -d 0x)
EOF


echo "signing p256 certificate.."
openssl x509 -trustout -req -days 18250  -in test-key-p256.pem.csr  -out test-cert-p256.pem -sha256 -CA ../test-root-cert.pem -CAkey ../test-root-key.pem -extfile v3.ext -set_serial $serial
echo "done"


openssl x509 -in test-cert-p256.pem -text -noout

echo "Test p256 signature.."
echo "test data to sign xxx $RANDOM" > data.txt
openssl dgst -sha256 -sign test-key-p256.pem -out data.sig data.txt
openssl x509 -in test-cert-p256.pem -pubkey -noout > pubkey.pem
openssl dgst -sha256 -verify pubkey.pem -signature data.sig data.txt
(($? != 0)) && { printf '%s\n' "Need to check why signature isn't working"; exit 1; }
rm -f data.txt pubkey.pem data.sig

echo "Verify p256 chain.."
openssl verify -verbose -CAfile "../test-root-cert.pem" "test-cert-p256.pem"
(($? != 0)) && { printf '%s\n' "Need to check why signature isn't working"; exit 1; }

rm -f test-key-p256.pem.csr


openssl genpkey -algorithm ED25519 -out test-key-ed255.pem

openssl req -new -key test-key-ed255.pem -out test-key-ed255.pem.csr  -subj "/C=$country/ST=$state/O=$organization/OU=$unit/CN=$CN"

echo "signing ed255 certificate.."
openssl x509 -trustout -req -days 18250  -in test-key-ed255.pem.csr  -out test-cert-ed255.pem -sha256 -CA ../test-root-cert.pem -CAkey ../test-root-key.pem -extfile v3.ext -set_serial $serial
openssl x509 -in test-cert-ed255.pem -text -noout

rm -f test-key-ed255.pem.csr

echo "Verify chain ed255.."
openssl verify -verbose -CAfile "../test-root-cert.pem" "test-cert-ed255.pem"
(($? != 0)) && { printf '%s\n' "Need to check why signature isn't working"; exit 1; }

rm -f v3.ext

echo "Trussed attestation key and cert $serial created & signed."
echo "root: ../test-root-key.pem ../test-root-cert.pem"
echo "intermediate: test-key-{p256,ed255}.pem test-cert-{p256,ed255}.pem"

