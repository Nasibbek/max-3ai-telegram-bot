import os
import sys
import json
import asyncio

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PhoneCodeExpiredError

API_ID = 38828334
API_HASH = "0ce78aa086473d016693c143e499b63b"
STATE_FILE = "login_state.json"
ENV_FILE = ".env"

async def send_code(phone: str):
    phone = phone.strip().replace(" ", "").replace("-", "")
    print(f"[*] Telegram orqali {phone} raqamiga kod so'rovi yuborilmoqda...")
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    await client.connect()
    try:
        res = await client.send_code_request(phone)
        session_str = client.session.save()
        state = {
            "phone": phone,
            "phone_code_hash": res.phone_code_hash,
            "session": session_str
        }
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        print("✅ CODE_SENT_SUCCESS")
        print(f"Telegram {phone} raqamiga 5 xonali tasdiqlash kodini yubordi!")
    except Exception as e:
        print(f"❌ Xatolik yuz berdi: {e}")
        sys.exit(1)
    finally:
        await client.disconnect()

async def verify_code(code: str, password: str = ""):
    if not os.path.exists(STATE_FILE):
        print("❌ Xatolik: Oldin kod so'rovi yuborilmagan (login_state.json topilmadi)!")
        sys.exit(1)

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        state = json.load(f)

    phone = state["phone"]
    phone_code_hash = state["phone_code_hash"]
    saved_session = state["session"]

    print(f"[*] Kod tekshirilmoqda: {code} ({phone})...")
    client = TelegramClient(StringSession(saved_session), API_ID, API_HASH)
    await client.connect()

    try:
        try:
            await client.sign_in(phone=phone, code=code.strip(), phone_code_hash=phone_code_hash)
        except SessionPasswordNeededError:
            if not password:
                print("⚠️ 2FA_PASSWORD_NEEDED")
                print("Akkauntingizda 2FA (Ikki bosqichli bulut paroli) yoqilgan. Iltimos, parolingizni kiriting.")
                return
            print("[*] 2FA paroli kiritilmoqda...")
            await client.sign_in(password=password.strip())

        me = await client.get_me()
        final_session = client.session.save()

        # .env ga saqlash
        lines = []
        if os.path.exists(ENV_FILE):
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()

        has_session = False
        new_lines = []
        for line in lines:
            if line.startswith("TELEGRAM_STRING_SESSION="):
                new_lines.append(f"TELEGRAM_STRING_SESSION={final_session}\n")
                has_session = True
            elif line.startswith("TELEGRAM_API_ID="):
                new_lines.append(f"TELEGRAM_API_ID={API_ID}\n")
            elif line.startswith("TELEGRAM_API_HASH="):
                new_lines.append(f"TELEGRAM_API_HASH={API_HASH}\n")
            else:
                new_lines.append(line)

        if not has_session:
            new_lines.append(f"\nTELEGRAM_API_ID={API_ID}\n")
            new_lines.append(f"TELEGRAM_API_HASH={API_HASH}\n")
            new_lines.append(f"TELEGRAM_STRING_SESSION={final_session}\n")

        with open(ENV_FILE, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)

        print("✅ LOGIN_SUCCESS")
        print(f"Muvaffaqiyatli ulandi: {me.first_name} (@{me.username}) [ID: {me.id}]")
        print(f"TELEGRAM_STRING_SESSION .env fayliga saqlandi!")
    except PhoneCodeInvalidError:
        print("❌ Kod noto'g'ri kiritildi! Qaytadan urinib ko'ring.")
    except PhoneCodeExpiredError:
        print("❌ Kod muddati tugagan! Qaytadan kod so'rang.")
    except Exception as e:
        print(f"❌ Xatolik yuz berdi: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python login_helper.py send <phone> OR python login_helper.py verify <code> [password]")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == "send":
        phone_num = sys.argv[2] if len(sys.argv) > 2 else "+998940295456"
        asyncio.run(send_code(phone_num))
    elif cmd == "verify":
        code_val = sys.argv[2] if len(sys.argv) > 2 else ""
        pwd_val = sys.argv[3] if len(sys.argv) > 3 else ""
        asyncio.run(verify_code(code_val, pwd_val))
    else:
        print(f"Noma'lum buyruq: {cmd}")
