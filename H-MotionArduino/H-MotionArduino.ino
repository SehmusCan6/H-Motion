#include <Servo.h>

// === PIN DEFINITIONS ===
#define motorPin 9
#define servoPin 8
#define ledFan 10      // Blue LED (ON when FAN is active)
#define ledGreen 11    // Green LED (SYSTEM ON)
#define ledWhite 12    // White LED (currently unused)
#define ledButton 13   // Yellow LED (linked to button)
#define buttonPin 4    // Button input pin

Servo myServo;
bool systemActive = false;

void setup() {
  Serial.begin(9600);

  pinMode(motorPin, OUTPUT);
  pinMode(ledFan, OUTPUT);
  pinMode(ledGreen, OUTPUT);
  pinMode(ledWhite, OUTPUT);
  pinMode(ledButton, OUTPUT);
  pinMode(buttonPin, INPUT);

  myServo.attach(servoPin);
  myServo.write(90); // Start at center position

  // Initial state
  digitalWrite(ledFan, LOW);
  digitalWrite(ledGreen, LOW);
  digitalWrite(ledWhite, LOW);
  digitalWrite(ledButton, LOW);
}

void loop() {
  // === BUTTON LED CONTROL ===
  int buttonState = digitalRead(buttonPin);
  digitalWrite(ledButton, buttonState);  // ON if pressed, OFF otherwise

  // === SERIAL COMMANDS ===
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "SYSTEM ON") {
      systemActive = true;
      digitalWrite(ledGreen, HIGH);
    }
    else if (command == "SYSTEM OFF") {
      systemActive = false;
      digitalWrite(motorPin, LOW);
      digitalWrite(ledFan, LOW);
      digitalWrite(ledGreen, LOW);
    }

    if (systemActive) {
      if (command == "FAN_ON") {
        digitalWrite(motorPin, HIGH);
        digitalWrite(ledFan, HIGH);
      }
      else if (command == "FAN_OFF") {
        digitalWrite(motorPin, LOW);
        digitalWrite(ledFan, LOW);
      }
      else if (command.startsWith("SERVO:")) {
        int angle = command.substring(6).toInt();
        myServo.write(angle);
      }
    }
  }
}
