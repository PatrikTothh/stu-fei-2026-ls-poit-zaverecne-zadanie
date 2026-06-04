#include <Wire.h>
#include <BH1750.h>
#include <PID_v1.h>

BH1750 lightMeter;
double Setpoint, Input, Output;

// PID koeficienty
double Kp = 0.14, Ki = 0.14, Kd = 0.0001;

PID myPID(&Input, &Output, &Setpoint, Kp, Ki, Kd, DIRECT);

const int ledPin = 9;

void setup()
{
  Serial.begin(115200); // Nastavené na 115200 pre rýchlu odozvu
  Serial.setTimeout(10);
  Wire.begin();
  lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE);
  pinMode(ledPin, OUTPUT);

  Setpoint = 100.0; // Počiatočná hodnota luxov
  myPID.SetOutputLimits(0, 255);
  myPID.SetSampleTime(10);
  myPID.SetMode(AUTOMATIC);
}

void loop()
{
  // --- Príjem dát z webu ---
  if (Serial.available() > 0)
  {
    String rcv = Serial.readStringUntil('\n'); // Prečíta hodnotu z webu
    double noveLuxy = rcv.toDouble();          // Prevedie na číslo
    if (noveLuxy >= 0)
    {
      Setpoint = noveLuxy; // Prepise žiadanú hodnotu
    }
  }

  // --- PID regulácia ---
  Input = (double)lightMeter.readLightLevel();
  myPID.Compute();
  analogWrite(ledPin, (int)Output);

  // --- Formátovaný výpis pre Python (Setpoint,Input,Output) ---
  Serial.print(Setpoint);
  Serial.print(",");
  Serial.print(Input);
  Serial.print(",");
  Serial.println(Output);

  delay(50); // Mierne spomalenie, aby sme nezahltili Serial buffer
}