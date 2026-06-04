from flask import Flask, render_template, request, jsonify
import serial
import time
import threading

app = Flask(__name__)

# Globálna premenná, kde budeme držať posledné dáta z Arduina
data_z_arduina = {
    "setpoint": 0,
    "input": 0,
    "output": 0
}

ser = None  
monitoring_active = False

@app.route('/open_connection', methods=['POST'])
def open_connection():
    global ser
    try:
        if ser is None or not ser.is_open:
            ser = serial.Serial('COM6', 115200, timeout=1)
            time.sleep(2) 
            return jsonify({"status": "connected", "msg": "Systém pripravený"})
        return jsonify({"status": "already_connected", "msg": "Systém už beží"})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500

@app.route('/close_connection', methods=['POST'])
def close_connection():
    global ser, monitoring_active
    monitoring_active = False
    if ser and ser.is_open:
        ser.close()
        return jsonify({"status": "disconnected", "msg": "Systém deaktivovaný"})
    return jsonify({"status": "error", "msg": "Nepodarilo sa zatvoriť"})
    
# Funkcia, ktorá beží na pozadí a stále číta Serial
def read_serial():
    global data_z_arduina
    while True: # Beží stále
        if ser and ser.is_open: # Číta len ak je port skutočne otvorený
            try:
                while ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8').strip()
                    if line:
                        parts = line.split(',')
                        if len(parts) == 3:
                            data_z_arduina["setpoint"] = parts[0]
                            data_z_arduina["input"] = parts[1]
                            data_z_arduina["output"] = parts[2]
            except Exception as e:
                print(f"Chyba pri čítaní: {e}")
        time.sleep(0.1)

# Spustenie čítacieho vlákna
thread = threading.Thread(target=read_serial, daemon=True)
thread.start()

@app.route('/')
def index():
    return render_template('index.html')

monitoring_active = False  # Premenná na sledovanie stavu

@app.route('/get_data')
def get_data():
    if monitoring_active:
        return jsonify(data_z_arduina)
    else:
        # Ak je monitoring vypnutý, posielame nuly alebo pomlčky
        return jsonify({"setpoint": "---", "input": "---", "output": "---"})

@app.route('/start_monitoring', methods=['POST'])
def start_monitoring():
    global monitoring_active
    monitoring_active = True
    print("Monitoring zapnutý")
    return jsonify({"status": "active"})

@app.route('/stop_monitoring', methods=['POST'])
def stop_monitoring():
    global monitoring_active
    monitoring_active = False
    print("Monitoring vypnutý")
    return jsonify({"status": "inactive"})

@app.route('/set_led', methods=['POST'])
def set_led():
    hodnota = request.form.get('intenzita')
    if ser and hodnota:
        ser.write(f"{hodnota}\n".encode()) 
        print(f"Web nastavil nový Setpoint: {hodnota}")
        return jsonify({"status": "ok", "value": hodnota})
    return jsonify({"status": "error"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)