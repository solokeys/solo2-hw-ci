
## Dependencies

```bash
sudo apt install git pigpio libusb-1.0-0-dev
sudo apt-get install -y -qq llvm libc6-dev-armel-cross libclang-dev clang
```

```bash
pip3 install -r requirements.txt
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
sudo cp JLink_Linux_*/JLinkGDBServer /usr/local/bin/
```

Add this line to your `~/.bashrc`.  Double check the path.

```bash
export PATH="$PATH:/home/pi/JLink_Linux_V752b_arm"
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

