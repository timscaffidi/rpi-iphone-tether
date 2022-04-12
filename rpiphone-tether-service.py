# SPDX-FileCopyrightText: 2017 Tony DiCola for Adafruit Industries
# SPDX-FileCopyrightText: 2017 James DeVito for Adafruit Industries
# SPDX-License-Identifier: MIT

# This example is for use on (Linux) computers that are using CPython with
# Adafruit Blinka to support CircuitPython libraries. CircuitPython does
# not support PIL/pillow (python imaging library)!

import sys, signal, time, subprocess
from oled_display import OledDisplay
import socket
import fcntl
import struct
import psutil
import os
from humanize import naturalsize

def get_ip_address(ifname):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', bytes(ifname[:15], 'utf-8'))
        )[20:24])
    except:
        return None
    finally:
        s.close()

oled = OledDisplay()

def signal_handler(singal, frame):
    global oled
    oled.clear()
    oled.present()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

RXBytes = -1
TXBytes = -1

RXQueue = []
TXQueue = []

maxQueueLen = 24
downTime = 0
autoSleepTime = 5
autoSleepCountdown = 30

dirname = os.path.dirname(os.path.abspath(__file__))
routeCmd = os.path.join(dirname, 'eth1-to-eth0-route.sh')

while True:

    oled.clear()

    # Shell scripts for system monitoring from here:
    # https://unix.stackexchange.com/questions/119126/command-to-display-memory-usage-disk-usage-and-cpu-load
    IP = get_ip_address('eth0')
    CPU = psutil.cpu_percent()
    MemUsage = psutil.virtual_memory().percent

    # Get current eth0 network usage
    cmd = "cat /sys/class/net/eth0/statistics/rx_bytes"
    NewRXBytes = int(subprocess.check_output(cmd, shell=True).decode("utf-8"))
    cmd = "cat /sys/class/net/eth0/statistics/tx_bytes"
    NewTXBytes = int(subprocess.check_output(cmd, shell=True).decode("utf-8"))

    seconds = 2
    
    RXDiff = NewRXBytes - RXBytes if RXBytes >= 0 else 0
    TXDiff = NewTXBytes - TXBytes if TXBytes >= 0 else 0

    RXQueue.append(RXDiff)
    if len(RXQueue) > maxQueueLen:
        RXQueue.pop(0)

    TXQueue.append(TXDiff)
    if len(TXQueue) > maxQueueLen:
        TXQueue.pop(0)

    Eth0RX = naturalsize(RXDiff / seconds)
    Eth0TX = naturalsize(TXDiff / seconds)

    RXBytes = NewRXBytes
    TXBytes = NewTXBytes
    
    TotalRXBytes = naturalsize(RXBytes)
    TotalTXBytes = naturalsize(TXBytes)

    tetherStatus = None

    if os.path.isdir('/sys/class/net/eth1'):
        IP = get_ip_address('eth1') or IP

        if subprocess.run(['systemctl','is-active','dnsmasq', '--quiet']).returncode == 0:
            tetherStatus = 'UP'
            downTime = 0 # Reset connected
        else:
            if subprocess.run(['ping', '-c1', '8.8.8.8'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
                tetherStatus = '---'
                subprocess.call(routeCmd)

            else:
                tetherStatus = '.' * (downTime % 4)
                seconds = 0.05

    else:
        if subprocess.run(['systemctl','is-active','dnsmasq', '--quiet']).returncode == 0:
            tetherStatus = '-/-'
            subprocess.run(['systemctl', 'stop', 'dnsmasq', '--quiet'])
        else:
            tetherStatus = " x "
            seconds = 1
            if downTime > autoSleepTime:
                IP = "SYSTEM SHUTDOWN IN ..."
                tetherStatus = f"{(autoSleepTime + autoSleepCountdown) - downTime}"
            if downTime >= autoSleepTime + autoSleepCountdown:
                print("Shutting down!")
                subprocess.run(['shutdown', '-H', 'now'])
                oled.clear()
                oled.present()
                sys.exit(0)

    # Write four lines of text.
    oled.drawTextLine(0, 0, f"{IP}") 
    oled.drawTextLine(114, 0, f"{tetherStatus}") 
    oled.drawTextLine(0, 8, f"CPU {CPU} Mem {MemUsage}")
    oled.drawTextLine(0, 16, f"U {TotalRXBytes}")
    oled.drawTextLine(80, 16, f"{Eth0RX}")
    oled.drawTextLine(0, 24, f"D {TotalTXBytes}")
    oled.drawTextLine(80, 24, f"{Eth0TX}")

    # Draw the RX/TX Usage queues
    maxRx = 0
    maxTx = 0
    for i in range(len(RXQueue)):
        maxRx = max(RXQueue[i], maxRx)
        maxTx = max(TXQueue[i], maxTx)

    for i in range(len(RXQueue)):
        rxHeight = (RXQueue[i] / maxRx) * 8 if maxRx > 0 else 0
        oled.drawRectangle(52 + i, 16 + (8 - rxHeight), 1, rxHeight)
        txHeight = (TXQueue[i] / maxTx) * 8 if maxTx > 0 else 0
        oled.drawRectangle(52 + i, 24, 1, txHeight)

    # Display image.
    oled.present()
    time.sleep(seconds)
    downTime += 1


