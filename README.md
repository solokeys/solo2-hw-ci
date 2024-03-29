# Hardware CI tester for Solo 2

This is a runner for CI testing that runs on a Raspberry Pi hooked up to a test Solo 2.  It will:

1. Program it with the latest provisioning firmware.
2. Provision the device.
3. Program it with the latest firmware.
4. Test it against all of the fido2-tests over HID and NFC.

Right now it triggers off of any commit to this repo.

# Setting up a Raspberry Pi from release

DD the image in the latest release on this repo onto an SD card and boot a Raspberry Pi 4B off of it.

SSH into the Pi (pi, raspberry).

Go to solo2-hw-ci github settings -> Actions -> runners and add a new runner.  Follow the instructions exactly.

In the end, running `/home/pi/actions-runner/run.sh` should activate the runner, and is what an already set up systemd service will run at boot.

Reboot and you're Done!

# Creating a new Pi runner from scratch

First: Install the lite version of raspbian onto a Raspberry Pi 4B (no desktop).  

Before booting the Pi, write an empty file `/boot/ssh`
to the sdcard from a different computer, so that ssh will be enabled on the pi.

The default username and password: pi,raspberry.  The rest of the "from scratch" instructions will be carried out on the RPi.


## Dependencies on Pi

```bash
sudo apt install git pigpio libusb-1.0-0-dev python3-pip
sudo apt-get install -y -qq llvm libc6-dev-armel-cross libclang-dev clang pcscd pcsc-tools python3-setuptools swig gcc libpcsclite-dev python3-dev
```

```bash
pip3 install pigpio pytest fido2==0.8.1 pyscard pytest-ordering pytest-rerunfailures pytest-timeout seedweed>=1.0rc7 solo-python==0.0.27
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
Restart=always

[Install]
WantedBy=multi-user.target
```

Run:

```
# Enable the github runner to run at startup.
sudo systemctl enable github-runner.service
sudo systemctl status github-runner.service
```

Add this file to `/lib/systemd/system/nfc-off.service`

```
[Unit]
Description=Turn off nfc reader at boot to avoid beeps.
After=pcscd.service

[Service]
Type=oneshot
User=pi
ExecStart=/usr/bin/python3 /home/pi/solo2-hw-ci/control.py nfc-off

[Install]
WantedBy=multi-user.target
```

```
sudo systemctl enable nfc-off.service
sudo systemctl status nfc-off.service
```

Also enable the pigpiod service.

```
sudo systemctl enable pigpiod.service
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

Install Linux driver for the ACR1252 NFC reader.

```
wget https://www.acs.com.hk/download-driver-unified/11929/ACS-Unified-PKG-Lnx-118-P.zip
unzip ACS-Unified-PKG-Lnx-118-P.zip
cd ACS-Unified-PKG-Lnx-118-P/raspbian/buster && sudo apt install ./*.deb
```

Add entry to cron tab to restart daily at 4am (`sudo crontab -e`).

```
0 4 * * * /sbin/shutdown -r now
```

### Connections

Connect [10 pin ribbon connector](https://www.digikey.com/en/products/detail/samtec-inc/IDSD-05-D-20-00-T/3679935) to rightmode side of RPi header.  Connect single power circuit jumper to GPIO2.

![IMG_4970](https://user-images.githubusercontent.com/3942133/128653614-76b8a8a3-eb78-4070-80d1-02d4f69b3632.jpg)


Connect ribbon cable to test Solo 2.  Ensure Solo 2 is connected to power circuit ([link](https://www.amazon.com/USB-PowerControl-board-Raspberry-Arduinos/dp/B00VQLS09K)).

![IMG_4972](https://user-images.githubusercontent.com/3942133/128653652-3b2215af-d8ea-42a3-a7b9-1683e28a8139.jpg)

The power control jump should be soldered to pins 1+2 (on the backside) 
on the USB power switch.

![IMG_4973](https://user-images.githubusercontent.com/3942133/128653808-82a80a01-3089-4683-8c9e-b167109b1fd9.jpg)
![IMG_4974 (1)](https://user-images.githubusercontent.com/3942133/128653810-b8242e66-030d-4644-a1f0-75b92eb3d95b.jpg)

Connect NFC reader ACR1252 to USB on Pi and place under test Solo 2.

Connect Jlink programmer to Pi USB and apply [TC2030-CTX 6-Pin tag connect cable](https://www.tag-connect.com/product/tc2030-ctx-6-pin-cable-for-arm-cortex) to Solo 2.

Connect Ethernet from Pi to a DHCP enabled router with internet access.  Apply USB-C power source to Pi.
