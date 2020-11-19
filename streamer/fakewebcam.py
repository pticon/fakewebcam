#!/usr/bin/env python3
#
# Copyright (c) 2020 Pierre Lebleu <pme.lebleu@gmail.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import argparse
from configparser import ConfigParser
import cv2
import numpy
import os
import pyfakewebcam
import requests
import sys
import time
from typing import TypeVar


DEFAULT_CONFIG_FILE="./conf/fakewebcam.ini"


T_VideoCapture = TypeVar('cv2.VideoCapture')
T_ndarray = TypeVar('numpy.ndarray')


def parse_config_file(config_file : str) -> dict:
    """
        Parse the given config file and return its associated dictionary
    """
    try:
        config = ConfigParser()
        config.read(config_file)

        params = {
            "streaming" : "",
            "witdth"    : 0,
            "height"    : 0,
            "fps"       : 0,
            "loopback"  : "",
            "bodypix"   : "",
            "pid"       : ""
        }

        params["streaming"] = str(config["streaming"]["device"])
        params["width"] = int(config["streaming"]["width"])
        params["height"] = int(config["streaming"]["height"])
        params["fps"] = int(config["streaming"]["fps"])
        params["loopback"] = config["loopback"]["device"]
        params["bodypix"] = "http://" + config["bodypix"]["service_addr"] + ":" + \
                config["bodypix"]["service_port"]
        params["background"] = config["background"]["file"]
        params["pid"] = config["daemon"]["pid"]

        return params
    except Exception as e:
        print("ERROR: {}: {}".format(config_file, e))
        exit(1)


def configure_camera(params : dict) -> T_VideoCapture:
    """
        Configure the given camera
    """
    cap = cv2.VideoCapture(params['streaming'])
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, params['width'])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, params['height'])
    cap.set(cv2.CAP_PROP_FPS, params['fps'])

    return cap


def get_mask(frame : T_ndarray, bodypix_service : str) -> T_ndarray:
    """
        Get the mask or detect the person
    """
    _, data = cv2.imencode('.jpg', frame)
    req = requests.post(
        url = bodypix_service,
        data = data.tobytes(),
        headers = { 'Content-Type' : 'application/octet-stream' }
    )

    mask = numpy.frombuffer(req.content, dtype = numpy.uint8)
    mask = mask.reshape((frame.shape[0], frame.shape[1]))

    return mask


def capture(cap : T_VideoCapture, params : dict) -> None:
    """
        Capture a frame from the camera and replace the background
    """
    success, frame = cap.read()

    mask = get_mask(frame, params['bodypix'])
    max_height, max_width = frame.shape[:2]

    background = cv2.imread(params['background'])
    height, width = background.shape[:2]

    if max_height < height or max_width < width:
        background = cv2.resize(background, (max_width, max_height), interpolation=cv2.INTER_AREA)

    camera = pyfakewebcam.FakeWebcam(params['loopback'], params['width'], params['height'])
    while True:
        success, frame = cap.read()

        mask = get_mask(frame, params['bodypix'])

        inv_mask = 1 - mask

        for c in range(frame.shape[2]):
            frame[:,:,c] = frame[:,:,c] * mask + background[:,:,c] * inv_mask

        camera.schedule_frame(frame)


def do_daemonize(params) -> None:
    """Daemonize the process and write the PID into the file"""
    try:
        child = os.fork()
        if child > 0:
            with open(params['pid'], "w") as f:
                f.write(str(child))
                exit(0)
    except Exception as e:
        print(e)
        exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Populate a v4l2 device with frames grabbed from a camera after changing the background")
    parser.add_argument("-c", "--config-file", type=str, help="The configuration file (default: {})".format(DEFAULT_CONFIG_FILE))
    parser.add_argument("-f", "--foreground", help="Keep in foreground (do not daemonize)", action='store_true')

    args = parser.parse_args()
    if not args.config_file:
        args.config_file = DEFAULT_CONFIG_FILE

    params = parse_config_file(args.config_file)

    if not args.foreground:
        do_daemonize(params)

    cap = configure_camera(params)
    capture(cap, params)
