cat > check_status.py << 'EOF'
#!/usr/bin/env python3
import json, subprocess, os, sys, requests

CONF = os.path.join(os.path.dirname(__file__), 'telegram.conf')

def load_cfg():
    try:
        return json.load(open(CONF))
    except:
        sys.exit(0)    # no config → do nothing

def myria_status():
    out = subprocess.run(['myria-node','--status'], capture_output=True, text=True)
    return out.stdout.splitlines()

def alert(lines, bot, chat):
    msg = "⚠️ *Node alert!*\n" + "\n".join(lines)
    requests.post(
      f"https://api.telegram.org/bot{bot}/sendMessage",
      data={'chat_id':chat,'text':msg,'parse_mode':'Markdown'},
      timeout=10
    )

def main():
    cfg = load_cfg()
    lines = myria_status()
    ok1 = any("Current Cycle Status: running" in l for l in lines)
    ok2 = any("Myria Node Service is running!" in l for l in lines)
    if not (ok1 and ok2):
        alert(lines, cfg['bot_token'], cfg['chat_id'])

if __name__=='__main__':
    main()
EOF

chmod +x check_status.py
