#include <Wire.h>
#include <BH1750.h>
#include <PID_v1.h>

BH1750 lightMeter;

double Setpoint, Input, Output;

// PID koeficienty
double Kp = 0.14;
double Ki = 0.14;
double Kd = 0.0001;

// Inicializácia PID. DIRECT znamená, že regulátor funguje ako "kúrenie" 
// (ak je svetlo nízke, pridá výkon LED-ke)
PID myPID(&Input, &Output, &Setpoint, Kp, Ki, Kd, DIRECT);

const int ledPin = 9;

void setup() {
  Serial.begin(115200);
  Wire.begin();
  lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE);

  pinMode(ledPin, OUTPUT);

  // Nastavenia PID
  Setpoint = 200.0;           // Žiadaná hodnota luxov
  myPID.SetOutputLimits(0, 255); // Výstup obmedzíme na PWM rozsah Arduina
  myPID.SetSampleTime(10);   
  myPID.SetMode(AUTOMATIC);    // Zapnutie PID regulátora
}

void loop() {
  // Načítanie aktuálnej hodnoty zo senzora
  Input = (double)lightMeter.readLightLevel();

  // Knižnica sama kontroluje čas a počíta PID
  myPID.Compute();

  // Zápis výsledku na LED
  analogWrite(ledPin, (int)Output);

  // Výpis hodnôt do terminálu
  Serial.print("Ciel: "); Serial.print(Setpoint);
  Serial.print(" | Aktualne: "); Serial.print(Input);
  Serial.print(" | Výkon LED (PWM): "); Serial.println(Output);

  delay(10); // Rýchla slučka, PID si časovanie riadi samo vo vnútri
}