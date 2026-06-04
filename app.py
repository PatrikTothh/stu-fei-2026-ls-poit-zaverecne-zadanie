from flask import Flask, render_template, request, jsonify
import serial
import time
import threading
import json
from datetime import datetime

app = Flask(__name__)

# Globálna premenná, kde budeme držať posledné dáta z Arduina
data_z_arduina = {
    "setpoint": 0,
    "input": 0,
    "output": 0
}

ser = None  
monitoring_active = False
current_session_data = []
last_log_time = 0

@app.route('/get_status')
def get_status():
    global ser, monitoring_active
    is_connected = ser is not None and ser.is_open
    return jsonify({
        "connected": is_connected,
        "monitoring": monitoring_active
    })

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
    while True:
        # Čítame len vtedy, ak je port otvorený
        if ser and ser.is_open:
            try:
                # Prečítame všetky správy v buffri, aby sme nemali lag
                while ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8').strip()
                    if line:
                        parts = line.split(',')
                        if len(parts) == 3:
                            # Len aktualizujeme "posledný známy stav"
                            data_z_arduina = {
                                "setpoint": parts[0],
                                "input": parts[1],
                                "output": parts[2]
                            }
            except Exception as e:
                # Ak nastane chyba (napr. odpojený kábel), vypíšeme ju
                print(f"Chyba pri čítaní Serialu: {e}")
                time.sleep(1) # Počkáme sekundu pred ďalším pokusom
        
        # Malá pauza, aby sme nevyťažili procesor na 100%
        time.sleep(0.01)

# Spustenie čítacieho vlákna
thread = threading.Thread(target=read_serial, daemon=True)
thread.start()

@app.route('/')
def index():
    return render_template('index.html')

monitoring_active = False  # Premenná na sledovanie stavu

@app.route('/get_data')
def get_data():
    global data_z_arduina, current_session_data, monitoring_active
    
    # Ak je monitoring zapnutý, práve teraz (v túto sekundu) uložíme snapshot
    if monitoring_active and data_z_arduina["setpoint"] != "---":
        timestamp_ms = datetime.now().strftime("%H:%M:%S")
        
        # Vytvoríme kópiu aktuálnych dát s časovou pečiatkou
        entry = {
            "timestamp": timestamp_ms,
            "setpoint": data_z_arduina["setpoint"],
            "input": data_z_arduina["input"],
            "output": data_z_arduina["output"]
        }
        current_session_data.append(entry)
        print(f"Uložená vzorka do pamäte: {timestamp_ms}")

    return jsonify(data_z_arduina)


@app.route('/start_monitoring', methods=['POST'])
def start_monitoring():
    global monitoring_active, current_session_data
    current_session_data = [] # Vyčistiť staré dáta z predošlého merania
    monitoring_active = True
    print("Monitoring a logovanie spustené.")
    return jsonify({"status": "active"})

@app.route('/stop_monitoring', methods=['POST'])
def stop_monitoring():
    global monitoring_active, current_session_data
    monitoring_active = False
    
    if current_session_data:
        # Pripravíme finálny objekt pre tento "beh" (session)
        log_entry = {
            "datum": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "pocet_merani": len(current_session_data),
            "merania": current_session_data
        }
        
        # Zápis do súboru (append mode 'a' - pridá na koniec súboru)
        try:
            with open("logs.txt", "a", encoding="utf-8") as f:
                # json.dumps vytvorí jeden riadok z celého objektu
                f.write(json.dumps(log_entry) + "\n")
            print(f"Uložených {len(current_session_data)} meraní do logs.txt")
        except Exception as e:
            print(f"Chyba pri zápise do súboru: {e}")
        
        current_session_data = [] # Vymazať z pamäte po zápise
        
    return jsonify({"status": "inactive"})

@app.route('/get_log/<int:index>')
def get_log(index):
    try:
        with open("logs.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
            # Indexovanie v zoznamoch začína od 0, ale používateľ zadá 1, 2, 3...
            real_index = index - 1 
            
            if 0 <= real_index < len(lines):
                # Riadok je už uložený ako JSON string, tak ho len pošleme
                return lines[real_index]
            else:
                return jsonify({"error": "Záznam s týmto číslom neexistuje."}), 404
    except FileNotFoundError:
        return jsonify({"error": "Súbor s logmi ešte neexistuje. Najprv niečo odmerajte."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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