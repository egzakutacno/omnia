cat > notification_setup.py << 'EOF'
#!/usr/bin/env python3
import json, os, subprocess, sys

# auto‐install requests if missing
try:
    import requests
except ImportError:
    subprocess.run(['pip3', 'install', 'requests'], check=True)
    import requests

# paths & bot token
BASE = os.path.dirname(__file__)
CONF = os.path.join(BASE, 'telegram.conf')
BOT_TOKEN = '8160013041:AAFSJ9_SaV7zufjgAPT7Zj70f4eyplecEhQ'
# three runs a day: 6:00, 14:00, 22:00
CRON = f"0 6,14,22 * * * python3 {os.path.join(BASE, 'check_status.py')} >> /var/log/omnia-check.log 2>&1"

def install_cron():
    try:
        existing = subprocess.check_output(['crontab','-l'], stderr=subprocess.DEVNULL).decode()
    except subprocess.CalledProcessError:
        existing = ''
    if CRON not in existing:
        new = existing + CRON + "\n"
        p = subprocess.Popen(['crontab'], stdin=subprocess.PIPE)
        p.communicate(new.encode())
        print("→ Installed cron job")
    else:
        print("→ Cron job already present")

def prompt():
    ans = input("Do you want Telegram notifications? (y/N): ").strip().lower()
    if ans != 'y':
        print("Skipping Telegram setup.")
        return
    chat = input("Enter your Telegram Chat ID: ").strip()
    with open(CONF,'w') as f:
        json.dump({'bot_token':BOT_TOKEN,'chat_id':chat}, f)
    print(f"Wrote {CONF}")
    install_cron()
    print("✅ Notifications configured!")

if __name__=='__main__':
    prompt()
EOF

chmod +x notification_setup.py
