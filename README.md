
## Dependencies

```bash
sudo apt install git pigpio libusb-1.0-0-dev
```

```bash
pip3 install -r requirements.txt
```

Install uhubctl from source.

```
git clone https://github.com/mvp/uhubctl.git
cd uhubctl
make
sudo make install
```

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

