import uasyncio as asyncio
import machine, os, urequests, ubinascii, secret

CHECK_INTERVAL = 60 * 30  # kolla var 30:e minut

# ============
# GitHub helpers
# ============
def github_get(url):
    headers = {"User-Agent": "micropython-pico"}
    if getattr(secret, "GITHUB_TOKEN", None):
        headers["Authorization"] = f"token {secret.GITHUB_TOKEN}"
    r = urequests.get(url, headers=headers)
    if r.status_code != 200:
        txt = r.text
        r.close()
        raise RuntimeError("HTTP %s: %s" % (r.status_code, txt))
    data = r.json()
    r.close()
    return data

def download_file_from_github(filepath):
    url = f"https://api.github.com/repos/{secret.USER}/{secret.REPO}/contents/{filepath}?ref={secret.BRANCH}"
    data = github_get(url)
    if "content" not in data:
        raise RuntimeError("Ingen 'content' i svar för " + filepath)
    return ubinascii.a2b_base64(data["content"])

# ============
# Version helpers
# ============
def get_local_version():
    try:
        import version
        return version.VERSION
    except Exception:
        return None

def get_remote_version():
    raw = download_file_from_github("version.py")
    ns = {}
    exec(raw.decode(), ns)
    return ns.get("VERSION", None), raw

# ============
# OTA logic
# ============
async def ota_check():
    try:
        local_ver = get_local_version()
        remote_ver, remote_version_py = get_remote_version()
        print("Lokal version:", local_ver, "Remote version:", remote_ver)

        if local_ver != remote_ver and remote_ver is not None:
            print("Ny version hittad → uppdaterar...")

            # Backup main.py → main_old.py
            try:
                if "main.py" in os.listdir():
                    if "main_old.py" in os.listdir():
                        os.remove("main_old.py")
                    os.rename("main.py", "main_old.py")
            except Exception as e:
                print("Backup-fel:", e)

            # Ladda ner ny main.py (bootstrapper)
            new_main = download_file_from_github("main.py")
            with open("main.py", "wb") as f:
                f.write(new_main)

            # Ladda ner ny app_main.py (din riktiga app)
            new_app = download_file_from_github("app_main.py")
            with open("app_main.py", "wb") as f:
                f.write(new_app)

            # Ladda ner ny version.py
            with open("version.py", "wb") as f:
                f.write(remote_version_py)

            print("✅ Uppdatering klar – startar om")
            await asyncio.sleep(1)
            machine.reset()
        else:
            print("Ingen ny version")
    except Exception as e:
        print("OTA error:", e)

async def ota_worker():
    while True:
        await ota_check()
        await asyncio.sleep(CHECK_INTERVAL)

def rollback_if_broken():
    try:
        import app_main as test_app
        del test_app
        return
    except Exception as e:
        print("⚠️ Ny app trasig, rullar tillbaka:", e)
        try:
            if "main_old.py" in os.listdir():
                if "main.py" in os.listdir():
                    os.remove("main.py")
                os.rename("main_old.py", "main.py")
        except Exception as e2:
            print("Rollback misslyckades:", e2)
        machine.reset()