import json
import platform
import serial
import time
import threading
import MySQLdb  # Knižnica z cvičenia
from datetime import datetime
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# --- KONFIGURÁCIA ---
# Automatický port (Linux vs Windows)
PORT = '/dev/ttyACM0' if platform.system() != "Windows" else 'COM3'

# DB konfigurácia podľa tvojho zadania
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "passwd": "admin",
    "db": "poit_db"
}

# Globálne premenné
ser = None
monitoring_active = False
current_session_data = []
data_z_arduina = {"setpoint": "---", "input": "---", "output": "---"}

# --- DATABÁZOVÉ FUNKCIE ---
def get_db_connection():
    return MySQLdb.connect(**DB_CONFIG)

# --- SERIAL ČÍTANIE ---
def read_serial():
    global data_z_arduina
    while True:
        if ser and ser.is_open:
            try:
                while ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8').strip()
                    if line:
                        parts = line.split(',')
                        if len(parts) == 3:
                            data_z_arduina = {
                                "setpoint": parts[0],
                                "input": parts[1],
                                "output": parts[2]
                            }
            except Exception as e:
                print(f"Serial error: {e}")
        time.sleep(0.01)

thread = threading.Thread(target=read_serial, daemon=True)
thread.start()

# --- ROUTES ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/open_connection', methods=['POST'])
def open_connection():
    global ser
    try:
        if ser is None or not ser.is_open:
            ser = serial.Serial(PORT, 115200, timeout=1)
            time.sleep(2)
            return jsonify({"status": "connected"})
        return jsonify({"status": "already_connected"})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500

@app.route('/close_connection', methods=['POST'])
def close_connection():
    global ser, monitoring_active
    monitoring_active = False
    if ser and ser.is_open:
        ser.close()
        return jsonify({"status": "disconnected"})
    return jsonify({"status": "error"})

@app.route('/get_data')
def get_data():
    global data_z_arduina, current_session_data, monitoring_active
    if monitoring_active and data_z_arduina["setpoint"] != "---":
        entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "setpoint": data_z_arduina["setpoint"],
            "input": data_z_arduina["input"],
            "output": data_z_arduina["output"]
        }
        current_session_data.append(entry)
    return jsonify(data_z_arduina)

@app.route('/start_monitoring', methods=['POST'])
def start_monitoring():
    global monitoring_active, current_session_data
    current_session_data = []
    monitoring_active = True
    return jsonify({"status": "active"})

@app.route('/stop_monitoring', methods=['POST'])
def stop_monitoring():
    global monitoring_active, current_session_data
    monitoring_active = False
    
    if current_session_data:
        json_string = json.dumps({
            "datum": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "pocet_merani": len(current_session_data),
            "merania": current_session_data
        })
        
        # 1. Uloženie do SÚBORU (logs.txt)
        with open("logs.txt", "a") as f:
            f.write(json_string + "\n")
            
        # 2. Uloženie do MYSQL (BOD 7)
        try:
            db = get_db_connection()
            cursor = db.cursor()
            # Použijeme tvoje názvy stĺpcov: poznamka, data_json
            sql = "INSERT INTO serie_merani (poznamka, data_json) VALUES (%s, %s)"
            cursor.execute(sql, ("Séria meraní", json_string))
            db.commit()
            db.close()
            print("Dáta uložené do MySQL")
        except Exception as e:
            print(f"DB Error: {e}")
            
    return jsonify({"status": "inactive"})

# NAČÍTANIE Z DB (Pre tvoj nový tab Databáza)
@app.route('/get_db_log/<int:id>')
def get_db_log(id):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT data_json FROM serie_merani WHERE id = %s", (id,))
        row = cursor.fetchone()
        db.close()
        
        if row:
            # row[0] už obsahuje JSON string, Flask ho pošle ako response
            return row[0]
        else:
            return jsonify({"error": "ID nenájdené"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/get_log/<int:index>')
def get_log(index):
    try:
        # Uisti sa, že názov súboru sedí s tým, čo používaš v stop_monitoring
        with open("logs.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
            # Premeníme užívateľské indexovanie (od 1) na programátorské (od 0)
            real_index = index - 1 
            
            if 0 <= real_index < len(lines):
                # Riadok je už uložený ako JSON string, tak ho len vrátime
                return lines[real_index]
            else:
                return jsonify({"error": "Záznam s týmto číslom v súbore neexistuje."}), 404
    except FileNotFoundError:
        return jsonify({"error": "Súbor logs.txt nebol nájdený."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/set_led', methods=['POST'])
def set_led():
    hodnota = request.form.get('intenzita')
    if ser and hodnota:
        ser.write(f"{hodnota}\n".encode())
        return jsonify({"status": "ok"})
    return jsonify({"status": "error"}), 400

# Cache-control pre Linux prehliadač
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
