from flask import Flask, render_template, request, redirect
from instagrapi import Client
import threading
import time
import random
import json

app = Flask(__name__)
app.secret_key = "sujal_hawk_pro_2025"

# Global vars
status = {"running": False, "sent": 0, "threads": 0, "logs": [], "text": "Ready"}
config = {
    "mode": "username",          # username or session
    "username": "", "password": "", "sessionid": "",
    "thread_id": "", "messages": "", "delay": 10,
    "cycle": 40, "break": 30, "threads": 3
}

clients = []
workers = []

FAKE_DEVICES = [
    {"android_version": 13, "manufacturer": "Google", "model": "Pixel 7"},
    {"android_version": 14, "manufacturer": "Samsung", "model": "SM-S928B"},
    {"android_version": 13, "manufacturer": "Xiaomi", "model": "23049PCD8G"},
    {"android_version": 14, "manufacturer": "OnePlus", "model": "PJZ110"}
]

def log(msg):
    status["logs"].append(f"[{time.strftime('%H:%M:%S')}] {msg}")
    if len(status["logs"]) > 500:
        status["logs"] = status["logs"][-500:]

def bomber(cl, tid, msgs, delay, cycle, brk):
    cnt = 0
    while status["running"]:
        try:
            msg = random.choice(msgs)
            cl.direct_send(msg, thread_ids=[tid])
            cnt += 1
            status["sent"] += 1
            log(f"Sent #{status['sent']} → {msg[:50]}")
            if cnt % cycle == 0:
                log(f"Break {brk}s after {cycle} msgs")
                time.sleep(brk)
            time.sleep(delay * random.uniform(1.3, 2.1))
        except Exception as e:
            log(f"Error → {str(e)[:100]}")
            time.sleep(20)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        status["running"] = False
        time.sleep(1.5)
        status["logs"].clear()
        status["sent"] = 0
        clients.clear()
        workers.clear()

        # Save config
        config.update({
            "mode": request.form.get('mode', 'username'),
            "username": request.form.get('username', ''),
            "password": request.form.get('password', ''),
            "sessionid": request.form.get('sessionid', '').strip(),
            "thread_id": request.form['thread_id'],
            "messages": request.form['messages'],
            "delay": float(request.form.get('delay', 10)),
            "cycle": int(request.form.get('cycle', 40)),
            "break": int(request.form.get('break', 30)),
            "threads": int(request.form.get('threads', 3))
        })

        msgs_list = [m.strip() for m in config["messages"].split('\n') if m.strip()]
        tid = int(config["thread_id"])

        status["running"] = True
        status["text"] = "BOMBING ACTIVE"
        log("SPAMMER STARTED")

        for i in range(config["threads"]):
            cl = Client()
            cl.delay_range = [8, 20]
            cl.set_device(random.choice(FAKE_DEVICES))

            try:
                if config["mode"] == "session" and config["sessionid"]:
                    # SESSION ID LOGIN (2FA BYPASS)
                    cl.login_by_sessionid(config["sessionid"])
                    log(f"Thread {i+1} → Session ID Login OK")
                else:
                    cl.login(config["username"], config["password"])
                    log(f"Thread {i+1} → Username Login OK")
                clients.append(cl)

                t = threading.Thread(target=bomber, args=(cl, tid, msgs_list,
                                config["delay"], config["cycle"], config["break"]), daemon=True)
                t.start()
                workers.append(t)
            except Exception as e:
                log(f"Thread {i+1} Failed → {str(e)[:80]}")

        status["threads"] = len(clients)
        if not clients:
            status["text"] = "LOGIN FAILED"
            status["running"] = False

    return render_template('index.html', **status, config=config)

@app.route('/stop')
def stop():
    status["running"] = False
    log("SPAM STOPPED BY USER")
    status["text"] = "STOPPED"
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
