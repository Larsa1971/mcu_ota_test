import socket
import machine
import time
import network

start_time = time.ticks_ms()

def get_uptime():
    return "{:.1f} sek".format(time.ticks_diff(time.ticks_ms(), start_time) / 1000)

def get_status_html():
    wlan = network.WLAN(network.STA_IF)
    ip = wlan.ifconfig()[0] if wlan.isconnected() else "Ej ansluten"
    uptime = get_uptime()

    html_content = f"""\
<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="utf-8" />
    <title>Pico W Status</title>
    <style>
        body {{ font-family: sans-serif; padding: 20px; background:#f0f0f0; }}
        h1 {{ color: #333; }}
        a.button {{
            display: inline-block;
            padding: 10px 20px;
            margin: 10px 5px;
            background: #007aff;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
        }}
        a.button:hover {{ background: #005bb5; }}
        a.red-button {{ background: #d9534f; }}
        a.red-button:hover {{ background: #b52b24; }}
    </style>
</head>
<body>
    <h1>Pico W Status</h1>
    <p><strong>IP-adress:</strong> {ip}</p>
    <p><strong>Uptime:</strong> {uptime}</p>
    <a href="/ota" class="button">Starta OTA-uppdatering</a>
    <a href="/reboot" class="button red-button">Starta om enheten</a>
</body>
</html>
"""
    # Bygg komplett HTTP-respons med header + body
    response = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        "Connection: close\r\n"
        "\r\n" +
        html_content
    )
    return response

def get_simple_response(message="OK"):
    html_content = f"<html><body><h1>{message}</h1></body></html>"
    response = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        "Connection: close\r\n"
        "\r\n" +
        html_content
    )
    return response

def start_web_server(ota_callback=None):
    addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # tillåter återanvändning av port
    s.bind(addr)
    s.listen(1)
    print("Webbserver igång på http://{}".format(addr))

    while True:
        try:
            cl, addr = s.accept()
            cl.settimeout(5)
            print("Ny anslutning från", addr)

            try:
                cl_file = cl.makefile("rwb", 0)

                # Läs första request-linjen
                request_line = cl_file.readline()
                if not request_line:
                    cl.close()
                    continue

                request = request_line.decode("utf-8").strip()
                print("HTTP-request:", request)

                # Läs och ignorera resten av headers för att tömma buffer (viktigt!)
                while True:
                    header_line = cl_file.readline()
                    if not header_line or header_line == b'\r\n':
                        break

                if "GET /ota" in request:
                    cl.sendall(get_simple_response("OTA startad...").encode('utf-8'))
                    cl.close()
                    if ota_callback:
                        machine.Timer().init(mode=machine.Timer.ONE_SHOT, period=100, callback=lambda t: ota_callback())

                elif "GET /reboot" in request:
                    cl.sendall(get_simple_response("Startar om enheten...").encode('utf-8'))
                    cl.close()
                    machine.Timer().init(mode=machine.Timer.ONE_SHOT, period=100, callback=lambda t: machine.reset())

                else:
                    cl.sendall(get_status_html().encode('utf-8'))
                    cl.close()

            except Exception as e:
                print("Klientfel:", e)
                try:
                    cl.close()
                except:
                    pass

        except Exception as e:
            print("Webbserver-fel:", e)

