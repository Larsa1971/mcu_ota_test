import machine
import network
import secret
import time
import os

def wifi_connect(ssid, password, timeout=15):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(ssid, password)
        start = time.time()
        while not wlan.isconnected():
            if time.time() - start > timeout:
                return False
            time.sleep(0.5)
    return wlan.ifconfig()

try:
    ifconfig = wifi_connect(secret.WIFI_SSID, secret.WIFI_PASSWORD)
    print("WiFi ansluten:", ifconfig)
    
    if "app_main_old.py" in os.listdir() and "app_main.py" in os.listdir():
        try:
            with open("app_main.py") as f:
                compile(f.read(), "app_main.py", "exec")
            print("Fungerande app_main.py!")
        except Exception as e2:
            print("Fel i app_main.py – gör rollback")
            os.remove("app_main.py")
            os.rename("app_main_old.py", "main.py")
            await asyncio.sleep(1)
            machine.reset()
    
except Exception as e:
    print("WiFi-anslutning misslyckades:", e)
