#!/usr/bin/env python
# coding: utf-8

# In[7]:


import socket
import time
import multiprocessing as mp
from pynq.overlays.base import BaseOverlay
base = BaseOverlay("base.bit")


# In[8]:


get_ipython().run_cell_magic('microblaze', 'base.PMODA', '\n#include "gpio.h"\n#include "pyprintf.h"\n\n#//Function to turn on/off a selected pin of PMODA\nvoid write_gpio(unsigned int pin, unsigned int val){\n    if (val > 1){\n        pyprintf("pin value must be 0 or 1");\n    }\n    gpio pin_out = gpio_open(pin);\n    gpio_set_direction(pin_out, GPIO_OUT);\n    gpio_write(pin_out, val);\n}\n\n#//Function to read the value of a selected pin of PMODA\nunsigned int read_gpio(unsigned int pin){\n    gpio pin_in = gpio_open(pin);\n    gpio_set_direction(pin_in, GPIO_IN);\n    return gpio_read(pin_in);\n}\n\n#//Function will turn-off PMOD pin\nvoid resetPMODPins(unsigned int pin)\n{\n    write_gpio(pin, 0);\n}\n')


# In[9]:


# CONFIG PER BOARD
MY_IP = "192.168.0.179"          
MY_PORT = 5005             # server port on THIS PYNQ

PEER_IP = "00.00.00.00"   # other PYNQ IP
PEER_PORT = 5005           # other PYNQ server port

# Buttons: base overlay btns_gpio[0..3]
BTN_CONNECT = 0
BTN_BEEP    = 1
BTN_BYE     = 2

TONE_FREQ_HZ = 2000     # Tone Frequency
BEEP_TIME_S  = 0.5

# PMODA pin to use
GPIO_PIN = 1


# In[10]:


#  BUZZER
def play_tone(freq_hz: float, duration_s: float):
    """Generate a square wave on GPIO_PIN for duration_s seconds."""
    
    if freq_hz <= 0 or duration_s <= 0:
        return
    half = 1.0 / (2.0 * freq_hz)
    end_t = time.perf_counter() + duration_s
    val = 0
    while time.perf_counter() < end_t:
        val ^= 1
        write_gpio(GPIO_PIN, val)
        time.sleep(half)
    write_gpio(GPIO_PIN, 0)


# SERVER PROCESS 
def server_proc(stop_event: mp.Event):
    resetPMODPins(GPIO_PIN)

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((MY_IP, MY_PORT))     # bind all interfaces
    srv.listen(1)
    srv.settimeout(0.5)

    print(f"[SERVER] Listening on {MY_IP}:{MY_PORT}")

    conn = None
    buf = b""

    try:
        while not stop_event.is_set():
            if conn is None:
                try:
                    conn, addr = srv.accept()
                    conn.settimeout(0.5)
                    print(f"[SERVER] Client connected from {addr}")
                except socket.timeout:
                    continue

            # Read incoming data
            try:
                data = conn.recv(1024)
                if not data:
                    print("[SERVER] Client disconnected")
                    conn.close()
                    conn = None
                    buf = b""
                    continue
                buf += data

                # Parse newline-terminated messages
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    msg = line.decode(errors="ignore").strip().upper()

                    if msg == "BEEP":
                        print("[SERVER] BEEP received → buzzing 0.5s")
                        play_tone(TONE_FREQ_HZ, BEEP_TIME_S)

                    elif msg == "BYE":
                        print("[SERVER] BYE received → stopping")
                        stop_event.set()
                        break
                    else:
                        print(f"[SERVER] Unknown message: {msg}")

            except socket.timeout:
                continue
            except OSError:
                # socket error
                conn = None
                buf = b""

    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass
        try:
            srv.close()
        except Exception:
            pass
        resetPMODPins(GPIO_PIN)
        print("[SERVER] Terminated")


# In[11]:


# CLIENT PROCESS 
def client_proc(stop_event: mp.Event):
    base = BaseOverlay("base.bit")
    btns = base.btns_gpio

    sock = None

    def connect():
        nonlocal sock
        if sock is not None:
            return
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2.0)
            s.connect((PEER_IP, PEER_PORT))
            s.settimeout(0.5)
            sock = s
            print(f"[CLIENT] Connected to {PEER_IP}:{PEER_PORT}")
        except Exception as e:
            print(f"[CLIENT] Connect failed: {e}")
            try:
                s.close()
            except Exception:
                pass
            sock = None

    def send_line(line: str):
        nonlocal sock
        if sock is None:
            print("[CLIENT] Not connected")
            return
        try:
            sock.sendall((line + "\n").encode())
        except Exception as e:
            print(f"[CLIENT] Send failed: {e}")
            try:
                sock.close()
            except Exception:
                pass
            sock = None

    def disconnect_and_stop():
        nonlocal sock
        if sock is not None:
            try:
                send_line("BYE")
            except Exception:
                pass
            try:
                sock.close()
            except Exception:
                pass
            sock = None
        stop_event.set()

    prev = [0, 0, 0, 0]
    print("[CLIENT] Ready: BTN0=connect, BTN1=beep, BTN2=disconnect")

    try:
        while not stop_event.is_set():
            cur = [btns[i].read() for i in range(4)]

            # Rising edge detect
            if cur[BTN_CONNECT] and not prev[BTN_CONNECT]:
                connect()

            if cur[BTN_BEEP] and not prev[BTN_BEEP]:
                # each press triggers ~0.5 s tone remotely
                send_line("BEEP")

            if cur[BTN_BYE] and not prev[BTN_BYE]:
                disconnect_and_stop()
                break

            prev = cur
            time.sleep(0.02)  # debounce-ish polling

    finally:
        if sock is not None:
            try:
                sock.close()
            except Exception:
                pass
        print("[CLIENT] Terminated")


# In[12]:


# MAIN 
def main():
    try:
        mp.set_start_method("fork")
    except RuntimeError:
        pass

    stop_event = mp.Event()

    ps = mp.Process(target=server_proc, args=(stop_event,), daemon=True)
    pc = mp.Process(target=client_proc, args=(stop_event,), daemon=True)

    ps.start()
    pc.start()

    # Wait until stop_event is set, then join
    try:
        while not stop_event.is_set():
            time.sleep(0.1)
    except KeyboardInterrupt:
        stop_event.set()

    pc.join(timeout=2.0)
    ps.join(timeout=2.0)
    print("[MAIN] Exiting")


if __name__ == "__main__":
    main()


# In[ ]:




