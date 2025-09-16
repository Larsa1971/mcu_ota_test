import uasyncio as asyncio
import ota
import web_server

import time
print("main.py körs")
time.sleep(1)

async def main():
    # Kolla att koden fungerar, annars rollback
    ota.rollback_if_broken()

    # Starta OTA-worker
    asyncio.create_task(ota.ota_worker())
    
    await asyncio.sleep(1)
        # Starta webbserver efter OTA-check
    web_server.start_web_server()


    # Starta din riktiga applikation
    import app_main
    await app_main.run()

try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()
