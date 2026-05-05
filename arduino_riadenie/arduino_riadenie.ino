// Definícia pinu pre LED (musí to byť PWM pin, napr. 3, 5, 6, 9, 10, 11)
const int ledPin = 9; 

void setup() {
  // Inicializácia sériovej komunikácie rýchlosťou 9600 baudov
  Serial.begin(9600);
  
  // Nastavenie pinu ako výstup
  pinMode(ledPin, OUTPUT);
  
  Serial.println("System pripraveny.");
  Serial.println("Zadaj cislo od 0 do 255 pre intenzitu LED:");
}

void loop() {
  // Kontrola, či prišli nejaké dáta cez sériovú linku
  if (Serial.available() > 0) {
    // Prečítanie zadaného čísla
    int intenzita = Serial.parseInt();

    // Ošetrenie vstupu, aby bol v rozsahu 0 - 255
    if (intenzita >= 0 && intenzita <= 255) {
      // Zápis PWM hodnoty na LED pin
      analogWrite(ledPin, intenzita);
      
      Serial.print("Nastavena intenzita: ");
      Serial.println(intenzita);
    } else {
      // Ignorujeme nuly, ktoré parseInt vráti pri prázdnom riadku (timeout)
      if (intenzita != 0 || Serial.peek() != -1) {
         // Serial.println("Chyba: Zadaj hodnotu v rozsahu 0 az 255!");
      }
    }
  }
}