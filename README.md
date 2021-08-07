
## Dependencies on Pi

```bash
sudo apt install git pigpio libusb-1.0-0-dev python3-pip
sudo apt-get install -y -qq llvm libc6-dev-armel-cross libclang-dev clang pcscd pcsc-tools python3-setuptools swig gcc libpcsclite-dev python3-dev
```

```bash
pip3 install pigpio pytest fido2==0.8.1 pyscard pytest-ordering pytest-rerunfailures seedweed>=1.0rc7 solo-python==0.0.27
pip3 install cbor2 asn1 asn1crypto pyscard ecdsa cryptography --upgrade
```

## Raspberry Pi setup

Go to solo2-hw-ci github settings -> Actions -> runners and add a new runner.  Follow the exact same instructions.

Add this file to `/lib/systemd/system/github-runner.service`

```
[Unit]
Description=Example systemd service.

[Service]
Type=simple
User=pi
ExecStart=/bin/bash /home/pi/actions-runner/run.sh

[Install]
WantedBy=multi-user.target
```

Run:

```
# Enable the github runner to run at startup.
sudo systemctl status github-runner.service
```

Install JLink gdb server.

```bash
wget --post-data 'accept_license_agreement=accepted&non_emb_ctr=confirmed&submit=Download+software' https://www.segger.com/downloads/jlink/JLink_Linux_arm.tgz
tar xvf JLink_Linux_arm.tgz
cd JLink_Linux_*_arm
sudo ln -s `pwd`/JLinkGDBServer /usr/bin/JLinkGDBServer
```

Add udev rules for solo hid devices.  Open `/etc/udev/rules.d/70-solokeys.rules` and add:

```bash
# Solo bootloader + firmware access
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="a2ca", TAG+="uaccess"
SUBSYSTEM=="tty", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="a2ca", TAG+="uaccess"

# Solo 2 bootloader + firmware access
KERNEL=="hidraw*", GROUP="input", MODE="0660"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="1209", ATTRS{idProduct}=="beee", TAG+="uaccess"
KERNEL=="hidraw*", GROUP="input", MODE="0660"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="1209", ATTRS{idProduct}=="b000", TAG+="uaccess"

# Unprovisioned Solo 2 bootloader access
KERNEL=="hidraw*", GROUP="input", MODE="0660"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="1fc9", ATTRS{idProduct}=="0021", TAG+="uaccess"

# Jlink
SUBSYSTEM=="usb", ATTRS{idVendor}=="1366", ATTRS{idProduct}=="010[1234]", MODE="664", GROUP="input"   

# ST DFU access
SUBSYSTEM=="usb", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="df11", TAG+="uaccess"

# U2F Zero
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="8acf", TAG+="uaccess"
```

run `sudo udevadm control --reload-rules && sudo udevadm trigger`.

Copy this repo's version of `Info.plist` that has Solo 2 added for PCSC.

```
sudo cp Info.plist /usr/lib/pcsc/drivers/ifd-ccid.bundle/Contents/Info.plist
sudo systemctl restart pcscd
```

### Connections

- Red + brown of ribbon connector is on the edge of pin header of RPi

### Prereqs

1. Build & sign the provisioner firmware.
2. Build & sign the application firmware.

### Steps

1. Enter bootrom if not already.
	- Assert pin & reset power.
2. Provision the keystore.
	- Run lpc55 provision <config>
3. Program provisioner firmware.
	- Run lpc55 receive-sb-file <provisioner.sb2>
	- Run lpc55 reset
4. Provision solo2 (with python script or solo2?).
5. Enter bootrom.
	- Use solo2 app mgmt bootrom
6. Program solo2 firmware.
	- Run lpc55 receive-sb-file <solo2.sb2>
7. Run fido2-tests, run <other-tests>

### Raspberry Pi setup

Install the lite version of raspbian onto a Pi (no desktop).  Before booting the Pi, write an empty file `/boot/ssh`
to the sdcard from a different computer, so that ssh will be enabled on the pi.

default username,password: pi,raspberry

