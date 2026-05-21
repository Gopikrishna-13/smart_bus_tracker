import json
import os
import smtplib
from email.mime.text import MIMEText

import firebase_admin
from firebase_admin import credentials, db
from flask import Flask, jsonify, request, send_from_directory
from flask_socketio import SocketIO

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'bustrack-secret-2024'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Firebase init — reads from environment variable on Render/Azure
key_json = json.loads(os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON', '{}'))
cred = credentials.Certificate(key_json)
firebase_admin.initialize_app(cred, {
    'databaseURL': os.environ.get('https://bus-tracker-c1dc9-default-rtdb.firebaseio.com', '')
})

subscribers = []

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/update', methods=['POST'])
def update_bus():
    data = request.json
    ref = db.reference('buses/bus1')
    ref.set(data)
    socketio.emit('bus_update', data)
    if data.get('delayed', False):
        send_delay_alerts(data)
    return jsonify({'status': 'ok'})

@app.route('/bus', methods=['GET'])
def get_bus():
    ref = db.reference('buses/bus1')
    data = ref.get()
    return jsonify(data or {})

@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.json.get('email', '').strip()
    if email and email not in subscribers:
        subscribers.append(email)
        return jsonify({'status': 'subscribed', 'email': email})
    return jsonify({'status': 'already_subscribed'})

def send_delay_alerts(data):
    if not subscribers:
        return
    smtp_user = os.environ.get('SMTP_USER')
    smtp_pass = os.environ.get('SMTP_PASS')
    if not smtp_user or not smtp_pass:
        print("[Alert] No SMTP credentials — skipping email")
        return
    try:
        body = (
            f"Bus {data['bus_id']} is currently delayed.\n\n"
            f"Route    : {data['route']}\n"
            f"At stop  : {data['current_stop']}\n"
            f"Next     : {data['next_stop']}\n"
            f"ETA      : {data['eta']} minutes\n"
            f"Time     : {data['timestamp']}\n"
        )
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(smtp_user, smtp_pass)
            for email in subscribers:
                msg = MIMEText(body)
                msg['Subject'] = f"Bus Delay Alert - {data['bus_id']}"
                msg['From'] = smtp_user
                msg['To'] = email
                server.send_message(msg)
    except Exception as e:
        print(f"[Alert] Email error: {e}")

if __name__ == '__main__':
    print("Starting Smart Bus Tracker...")
    print("Open http://localhost:5000 in your browser")
    socketio.run(app, debug=False, host='0.0.0.0', port=5000, use_reloader=False)