import network
import time
import secret

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
except Exception as e:
    print("WiFi-anslutning misslyckades:", e)