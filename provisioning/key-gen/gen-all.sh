set -ex

./gen-test-root-key.sh

rm -rf fido2 && mkdir fido2
cd fido2
../gen-test-fido-ca-intermediate.sh
cd ..

rm -rf trussed && mkdir trussed
cd trussed
../gen-test-trussed-ca-intermediate.sh
cd ..
