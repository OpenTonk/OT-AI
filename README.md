# OT-AI
AI driven tonk driver

# install
```
sudo apt install python3 python3-pip
git clone https://github.com/OpenTonk/OT-AI.git
cd OT-AI
pip3 install -r requirements.txt
```
//picamera
//picamera[array]

## run
### server
```
python3 OT-AI/server.py -a <ip> -p <port> (--usepicam --save --record)
```
### client
```
python3 OT-AI/client.py
```