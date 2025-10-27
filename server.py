from flask import Flask,request, jsonify
import os
from datetime import datetime

app = Flask(__name__)
RECEIVED_DIR = "received_logs"
os.makedirs(RECEIVED_DIR, exist_ok=True)

@app.route("/upload", methods = ["POST"])
def upload():
    payload = request.get_json()
    if not payload or "data" not in payload or "timestamp" not in payload:
        return jsonify({"status":"error","reason":"bad payload"}), 400

    token_b64 = payload["data"]
    ts = payload["timestamp"]
    filename = f"recv_{ts.replace(':','-').replace(' ','_')}.b64"
    path = os.path.join(RECEIVED_DIR, filename)

    with open(path, "w") as f:
        f.write(token_b64)

    print(f"[{datetime.now()}] Received and saved {filename}")
    return jsonify({"status":"ok"}), 200

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)