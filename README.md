# fake_webcam

*fake_webcam* is a simple tool allowing you to change the background from your webcam.
The project is composed with several parts:
- config: a configuration file allowing you to tweak all of the parameters
- microservice: a NodeJS service used to detect person with BodyPix
- module: a kernel module used to create a video loopback
- core: a python script grabbing the frame, changing the background using the microservice and populating a video loopback
- init: an init script acting as a glue in order to create a service


## Prerequisites
Some dependencies are required in order to use the project.

### Automated install
The automated install is only supported for debian like distribution.
Please run the script *install.sh* as root:
```
sudo ./install.sh
```

### Manual install
Some tools are required, you have to install:
- *docker*
- *python3*
- *python3-opencv*
- *v4l2loopback-dkms*
```
sudo apt-get install docker python3 v4l2loopback-dkms python3-opencv
```
- *pyfakewebcam*
```
sudo pip install pyfakewebcam
```

Optional tools for recording and playing: *ffmpeg*
```
sudo apt-get install ffmpeg
```

Please adapt those commands toward your Linux flavor.


## Structure
The projet follows a tree for the directories:
```
.
├── background
│   └── linux.jpg
├── bg_changer
│   ├── app.js
│   ├── Dockerfile
│   └── package.json
├── conf
│   └── fakewebcam.ini
├── install.sh
├── LICENSE
├── README.md
├── service.py
└── streamer
    └── fakewebcam.py
```

### top level
There is a python script *service.py* which acts as a glue between the
component. The end user should interact only with this script.

### background
This is where you should put your background files used by the project.
Feel free to extend the directory by adding yours there.

### bg_changer
This is where the microservice takes place.
- app.js : this is the NodeJS script acting as a microservice
- Dockerfile : this is the file used to create the docker
- package.json : this is the file used by docker to fetch bodypix

### conf
This is where the configuration file stands. One is already given as an example.
Feel free to tweak the configuration.

### streamer
This is where the streamer stands. This is a python script which grabs frames from
the streaming camera and then change the background and finally populate the loopback.

## Usage

### Overview
First of all, you need to build the docker image for the microservice:
```
./service.py build
```

After this, you can start the whole service:
```
sudo ./service.py start
```

Then, you can stop the service:
```
sudo ./service.py stop
```

Finally, you can clean your docker image:
```
./service.py clean
```

More help can be found:
```
./service.py
```

### Trouble shooting
Make sure the docker is correctly build and available.
```
docker images
```

Make sure the v4l2loopback module is available and you can load it.
```
sudo modprobe v4l2loopback
```

## Tips
Video can be recorded with:
```
ffmpeg -f video4linux2 -i /dev/video10 test_fakewebcam.mpg
```

Video can be played directly from device:
```
vlc v4l2:///dev/video10:width=640:height=480
vlc v4l2:///dev/video10
```

Camera formats can be queried with:
```
v4l2-ctl -d /dev/video0 --list-formats-ext
```

## License
*fakewebcam* is licensed under the BSD 3-clause license.
