import os
import subprocess
import time
devmem_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "bin", "devmem2")
import logging

def enable_usb(enable):
    if enable:
        # Enable usb
        try:
            with open("/sys/bus/usb/drivers/usb/bind", "a") as f:
                f.write("usb1")
            time.sleep(1)
        except IOError:
            logging.info("Device already enabled")

        subprocess.call([devmem_path, "0x47401c60", "b", "0x01"])
        time.sleep(5)  # Wait until usb is fully initialized

    else:
        # Disable usb
        subprocess.call([devmem_path, "0x47401c60", "b", "0x00"])
        time.sleep(1)
        try:
            with open("/sys/bus/usb/drivers/usb/unbind", "a") as f:
                f.write("usb1")
        except IOError:
            logging.info("Device already disabled")


def enable_network(enable):
    if enable:
        subprocess.call(["/sbin/ifup", "wlan0"])
    else:
        subprocess.call(["/sbin/ifdown", "wlan0"])

