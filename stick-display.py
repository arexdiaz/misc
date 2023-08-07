#!/usr/bin/python3
# -*- coding:utf-8 -*-

from PIL import Image, ImageDraw, ImageFont
import epd2in13_V2
import subprocess
import psutil
import socket
import logging
import time
import os

picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "epaper/pic")
font_path = os.path.join(picdir, "Font.ttc")

logger = logging.getLogger("my_logger")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler("error.log")
handler.setLevel(logging.ERROR)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect("/tmp/pisugar-server.sock")

def get_ip_address(ifname):
    output = subprocess.run(["ip", "-4", "addr", "show", ifname], capture_output=True, text=True, universal_newlines=True)
    if output.returncode == 0:
        try:
            ipaddr = output.stdout.split("inet ")[1].split("/")[0]
        except IndexError:
            ipaddr = "Not connected"
        return ipaddr
    else:
        ipaddr = "Not connected"
    return ipaddr

def is_hostapd_running():
    for proc in psutil.process_iter(["name"]):
        if proc.info["name"] == "hostapd":
            return True
    return False

def hostap():
    if is_hostapd_running():
        return "ON"
    else:
        return "OFF"

def get_ssid():
    command = "/sbin/iw wlan0 info | grep ssid | awk '{print $2}'"
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, _ = process.communicate()
    if not stdout.strip().decode("utf-8"):
        return "Not connected"
    return stdout.strip().decode("utf-8")

def get_battery_status(sock):
    try:
        sock.sendall(b"get battery")
        data = sock.recv(1024)
        bat = data.decode("utf-8").strip()
        num = round(float(bat.split("battery: ")[1]))
        return num
    except:
        return "--"

try:
    epd = epd2in13_V2.EPD()
    epd.init(epd.FULL_UPDATE)
    epd.Clear(0xFF)

    font24 = ImageFont.truetype(font_path, 24)
    font20 = ImageFont.truetype(font_path, 20)

    time_image = Image.new("1", (epd.height, epd.width), 255)
    time_draw = ImageDraw.Draw(time_image)

    epd.init(epd.FULL_UPDATE)
    epd.displayPartBaseImage(epd.getbuffer(time_image))

    epd.init(epd.PART_UPDATE)

    while (True):
        time_draw.rectangle((0, 0, 250, 145), fill = 255)
        time_draw.text((2, 0), "eth0: " + get_ip_address("eth0"), font = font20, fill = 0)
        time_draw.text((2, 20), "wlan0: " + get_ip_address("wlan0"), font = font20, fill = 0)

        time_draw.text((2, 40), "SSID: " + get_ssid(), font = font20, fill = 0)
        time_draw.text((2, 60), "AP: " + hostap(), font = font20, fill = 0)

        time_draw.text((160, 95), time.strftime("%H:%M:%S"), font = font24, fill = 0)
        time_draw.text((2, 95), str(get_battery_status(sock))+"%", font = font24, fill = 0)

        epd.displayPartial(epd.getbuffer(time_image))
        time.sleep(1)

except:
    sock.close()
    logger.error("Exception occurred", exc_info=True)
    epd2in13_V2.epdconfig.module_exit()
    exit()
