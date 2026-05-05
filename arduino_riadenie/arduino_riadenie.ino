const int ledPin = 9;

void setup() {
  Serial.begin(9600);
  pinMode(ledPin, OUTPUT);
  Serial.println("System pripraveny.");
}

void loop() {
  // Kontrola, či prišli nejaké dáta
  if (Serial.available() > 0) {
    // Prečítame celý reťazec až po znak nového riadku '\n'
    String input = Serial.readStringUntil('\n');
    
    // Odstránime prípadné medzery (white spaces)
    input.trim();

    // Ak reťazec nie je prázdny
    if (input.length() > 0) {
      int intenzita = input.toInt(); // Prevedieme na celé číslo

      // Ošetrenie rozsahu
      if (intenzita >= 0 && intenzita <= 255) {
        analogWrite(ledPin, intenzita);
        
        // Spätná väzba pre Python (uvidíš v konzole VS Code)
        Serial.print("Arduino nastavilo jas na: ");
        Serial.println(intenzita);
      }
    }
  }
}