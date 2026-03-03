"""
WebSocket Appointments Channel — Debug Test Script
===================================================
Run on the production droplet:

    python debug_ws_appointments.py

Or with an explicit token:

    python debug_ws_appointments.py 2f2e4f1938f1fa98d1e47c5de8cddb7d150635ea
"""

import asyncio
import json
import sys
import websockets

# ──────────────────────────────────────────────────────────────────────────────
# Config — edit these if needed
# ──────────────────────────────────────────────────────────────────────────────
TOKEN  = sys.argv[1] if len(sys.argv) > 1 else "2f2e4f1938f1fa98d1e47c5de8cddb7d150635ea"
HOST   = "dzmedilink.duckdns.org"
ORIGIN = "https://dzmedilink.netlify.app"

NOTIFICATIONS_URL = f"wss://{HOST}/ws/notifications/?token={TOKEN}"
APPOINTMENTS_URL  = f"wss://{HOST}/ws/appointments/?token={TOKEN}"
HEADERS = {"Origin": ORIGIN}


async def test_channel(label: str, url: str, wait_seconds: int = 5) -> bool:
    """Connect, receive the first message, listen for `wait_seconds`, then disconnect."""
    print(f"\n{'='*60}")
    print(f"  Channel : {label}")
    print(f"  URL     : {url}")
    print(f"{'='*60}")

    try:
        async with websockets.connect(url, additional_headers=HEADERS) as ws:
            print(f"  ✅  Handshake OK — connected")

            # Read the initial server push (should arrive immediately)
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=5)
                msg = json.loads(raw)
                print(f"  📩  First message : {json.dumps(msg, indent=4)}")
            except asyncio.TimeoutError:
                print(f"  ⚠️   No initial message within 5 s (server may only push on events)")

            # Keep listening for further events
            print(f"\n  Listening for additional events for {wait_seconds}s …")
            print(f"  (Trigger an appointment action in another terminal or the UI)\n")
            deadline = asyncio.get_event_loop().time() + wait_seconds
            while True:
                remaining = deadline - asyncio.get_event_loop().time()
                if remaining <= 0:
                    break
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=remaining)
                    msg = json.loads(raw)
                    print(f"  📩  Event received : {json.dumps(msg, indent=4)}")
                except asyncio.TimeoutError:
                    break
                except websockets.ConnectionClosed as e:
                    print(f"  ❌  Connection closed unexpectedly: {e}")
                    return False

            print(f"\n  ✅  Test complete — channel is working")
            return True

    except websockets.exceptions.InvalidStatus as e:
        print(f"  ❌  Server rejected connection: {e}")
        if "403" in str(e):
            print("      → 403 Forbidden: token is invalid/expired or Origin not allowed")
        elif "401" in str(e):
            print("      → 401 Unauthorized: token wasn't accepted")
        return False
    except OSError as e:
        print(f"  ❌  Network error: {e}")
        print("      → Is Daphne running?  sudo systemctl status daphne")
        return False
    except Exception as e:
        print(f"  ❌  Unexpected error: {type(e).__name__}: {e}")
        return False


async def main():
    print("\n🔌  MediLink WebSocket Diagnostic Tool")
    print(f"    Token  : {TOKEN[:10]}…{TOKEN[-6:]}")
    print(f"    Host   : {HOST}")
    print(f"    Origin : {ORIGIN}")

    # Test notifications first (known working)
    notif_ok = await test_channel("notifications", NOTIFICATIONS_URL, wait_seconds=3)

    # Test appointments
    appt_ok  = await test_channel("appointments",  APPOINTMENTS_URL, wait_seconds=10)

    print(f"\n{'='*60}")
    print(f"  Summary")
    print(f"{'='*60}")
    print(f"  notifications channel : {'✅  PASS' if notif_ok else '❌  FAIL'}")
    print(f"  appointments  channel : {'✅  PASS' if appt_ok  else '❌  FAIL'}")

    if not appt_ok:
        print("""
  Troubleshooting checklist:
  1. Check Daphne routing — does /ws/appointments/ exist?
       grep -r "ws/appointments" ~/backend/medilink_backend/
  2. Check Daphne logs:
       sudo journalctl -u daphne -n 50
  3. Check Nginx proxies /ws/appointments/:
       sudo nginx -T | grep appointments
  4. Restart services after any code change:
       sudo systemctl restart daphne
""")


asyncio.run(main())
