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

# Nastavenie sériovej komunikácie
try:
    ser = serial.Serial('COM6', 115200, timeout=1)
    time.sleep(2)
    print("Pripojenie k Arduinu bolo úspešné!")
except Exception as e:
    print(f"Chyba pripojenia: {e}")
    ser = None

# Funkcia, ktorá beží na pozadí a stále číta Serial
def read_serial():
    global data_z_arduina
    while ser and ser.is_open:
        try:
            # Ak je v buffri nahromadených veľa správ, prečítame ich všetky
            # ale spracujeme len tú poslednú
            while ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                
                if line:
                    parts = line.split(',')
                    if len(parts) == 3:
                        data_z_arduina["setpoint"] = parts[0]
                        data_z_arduina["input"] = parts[1]
                        data_z_arduina["output"] = parts[2]
            
            # Krátka pauza, aby sme nevyťažili procesor
            time.sleep(0.01) 
        except Exception as e:
            print(f"Chyba pri čítaní: {e}")
            time.sleep(1)

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