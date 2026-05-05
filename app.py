from flask import Flask, render_template, request, url_for, redirect
import serial
import time

app = Flask(__name__)

# Nastavenie sériovej komunikácie
try:
    ser = serial.Serial('COM3', 9600, timeout=1)
    time.sleep(2)
    print("Pripojenie k Arduinu bolo úspešné!")
except Exception as e:
    print(f"Skutočná chyba pripojenia: {e}")
    ser = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/set_led', methods=['POST'])
def set_led():
    intenzita = request.form.get('intenzita')
    if ser and intenzita:
        ser.write(f"{intenzita}\n".encode())
        return {"status": "ok", "value": intenzita}, 200 
    return {"status": "error"}, 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)