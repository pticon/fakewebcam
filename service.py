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

from configparser import ConfigParser
import os
import sys
import time


DEFAULT_CONFIG_FILE="./conf/fakewebcam.ini"


def parse_config_file(config_file : str) -> dict:
    """
        Parse the given config file and return its associated dictionary
    """
    try:
        config = ConfigParser()
        config.read(config_file)

        params = {
            "config_file" : config_file,
            "microservice_port" : "0",
            "loopback_nr" : "10",
            "loopback_name" : "Fakewebcam",
            "loopback_exclusive" : "1",
            "pid" : "/var/run/fakewebcam.pid",
        }

        params["config_file"] = os.path.realpath(config_file)
        params["microservice_port"] = config["bodypix"]["service_port"]
        params["loopback_nr"] = os.path.basename(config["loopback"]["device"]).split("video")[1]
        params["loopback_name"] = config["loopback"]["name"]
        params["loopback_exclusive"] = config["loopback"]["exclusive_caps"]
        params["pid"] = config["daemon"]["pid"]

        return params
    except Exception as e:
        print("ERROR: {}: {}".format(config_file, e))
        exit(1)


def check_root() -> None:
    """Check if the EUID is 0"""
    if os.geteuid() != 0:
        print("Please run as root")
        exit(1)

def build_docker(params) -> None:
    """Build the docker image used for the microservice"""
    print("Building docker image...")
    cmd = "cd bg_changer && docker build --tag bg_changer . >/dev/null 2>&1"
    if os.system(cmd) == 0:
        print(" Success !")
    else:
        print(" Failure !")


def clean(params) -> None:
    """Clean the docker images"""
    print("Cleaning docker image...")
    cmd = "docker rmi bg_changer >/dev/null 2>&1"
    if os.system(cmd) == 0:
        print(" Success !")
    else:
        print(" Failure !")

def start_microservice(params) -> None:
    """Start the docker containing the microservice"""
    print("Starting microservice...")
    cmd = "docker run --rm --publish " + params['microservice_port'] + ":" + \
        params['microservice_port'] + " --detach --name bg_changer " + \
        "--mount type=bind,source=" + params['config_file'] + \
        ",destination=/fakewebcam.ini bg_changer >/dev/null 2>&1"
    if os.system(cmd) == 0:
        print(" Success !")
    else:
        print(" Failure !")


def stop_microservice(params) -> None:
    """Stop the container associated to the microservice"""
    print("Stopping microservice...")
    if os.system("docker stop bg_changer >/dev/null 2>&1") == 0:
        print(" Success !")
    else:
        print(" Failure !")


def check_microservice(params) -> None:
    """Check if the container associated to the microservice is running"""
    cmd = "docker container inspect -f '{{.State.Running}}' bg_changer >/dev/null 2>&1"
    if os.system(cmd) == 0:
        print("Microservice is running")
    else:
        print("Microservice is NOT running")


def load_kernel_module(params) -> None:
    """Load the v4l2 kernel module"""
    print("Loading kernel module...")
    os.system("modprobe -r v4l2loopback >/dev/null 2>&1")
    cmd = "modprobe v4l2loopback devices=1 video_nr=" + params['loopback_nr'] + \
        " card_label=" + params['loopback_name'] + \
        " exclusive_caps=" + params['loopback_exclusive'] + " >/dev/null 2>&1"
    if os.system(cmd) == 0:
        print(" Success !")
    else:
        print(" Failure !")


def unload_kernel_module(params) -> None:
    """Unload the v4l2 kernel module"""
    print("Unloading kernel module...")
    if os.system("modprobe -r v4l2loopback >/dev/null 2>&1") == 0:
        print(" Success !")
    else:
        print(" Failure !")


def check_kernel_module(params) -> None:
    """Check if the v4l2 kernel module is loaded"""
    if os.system("lsmod | grep v4l2loopback >/dev/null 2>&1") == 0:
        print("Kernel module is loaded")
    else:
        print("Kernel module is NOT loaded")


def start_streamer(params) -> None:
    """Start the streamer program"""
    print("Starting streamer...")
    time.sleep(5)
    cmd = "./streamer/fakewebcam.py -c " + params["config_file"] + " >/dev/null 2>&1"
    if os.system(cmd) == 0:
        print(" Success !")
    else:
        print(" Failure !")


def stop_streamer(params) -> None:
    """Stop the streamer program"""
    print("Stopping streamer...")
    try:
        with open(params['pid'], 'r') as f:
            pid = f.read()
        cmd = "kill " + str(pid) + " >/dev/null 2>&1"
        if os.system(cmd) == 0:
            print(" Success !")
        else:
            print(" Failure !")
        os.remove(params['pid'])
    except Exception as e:
        print(" Failure !")


def check_streamer(params) -> None:
    """Check if the streamer is running"""
    try:
        with open(params['pid'], "r") as f:
            pid = f.read()
        if os.path.isdir("/proc/" + str(pid)):
            print("Streamer is running")
        else:
            print("Streamer is NOT running")
    except Exception as e:
        print("Streamer is NOT running")


def start(params) -> None:
    """Start the whole service"""
    check_root()
    start_microservice(params)
    load_kernel_module(params)
    start_streamer(params)


def stop(params) -> None:
    """Stop the whole service"""
    check_root()
    stop_streamer(params)
    unload_kernel_module(params)
    stop_microservice(params)


def usage() -> None:
    """Classical usage function"""
    print("usage: start.py <build|start|stop|status|restart|clean> [config]")
    exit(0)


if __name__ == "__main__":
    try:
        cmd = sys.argv[1]
        if len(sys.argv) >= 3:
            config_file = sys.argv[2]
        else:
            config_file = DEFAULT_CONFIG_FILE
    except Exception as e:
        usage()

    params = parse_config_file(config_file)

    if cmd == "build":
        build_docker(params)
    elif cmd == "start":
        start(params)
    elif cmd == "stop":
        stop(params)
    elif cmd == "status":
        check_microservice(params)
        check_kernel_module(params)
        check_streamer(params)
    elif cmd == "restart" or cmd == "reload":
        stop(params)
        time.sleep(5)
        start(params)
    elif cmd == "clean":
        clean(params)
    else:
        print("Unknown command {}".format(cmd))
        exit(1)
