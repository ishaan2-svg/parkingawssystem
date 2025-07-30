#include <WiFi.h>
#include <SPIFFS.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>
#include "utils.h"  // contains mqttClient and connectAWS()

// IR sensor pins
const int irEntry = 4;
const int irSlot1 = 19;
const int irSlot2 = 23;
const int irExit  = 5;

// LED pins
const int ledSlot1 = 22;
const int ledSlot2 = 15;

// Servo pins
const int servoEntryPin = 18;
const int servoExitPin  = 21;

Servo servoEntry;
Servo servoExit;

// Slot states
bool entryGateOpen = false;
bool exitGateOpen = false;
bool slot1Occupied = false;
bool slot2Occupied = false;

// void publishSlotStatus(const char* slotId, bool occupied) {
//   StaticJsonDocument<256> doc;
//   time_t now = time(nullptr);
//   doc["slot"] = slotId;
//   doc["status"] = occupied ? "occupied" : "vacant";
//   doc["timestamp"] = now;
//   doc["sessionId"] = String(slotId) + "#" + String(now);

//   char buffer[256];
//   serializeJson(doc, buffer);

//   Serial.println("📤 Publishing to AWS IoT:");
//   Serial.print("Topic: esp32/SmartParking/status\nPayload: ");
//   Serial.println(buffer);

//   if (mqttClient.connected()) {
//     mqttClient.publish("esp32/SmartParking/status", buffer);
//     Serial.println("✅ MQTT publish successful");
//   } else {
//     Serial.println("❌ MQTT not connected");
//   }
// }
#include <ArduinoJson.h>

void publishSlotStatus(const char* slotId, const char* vehicleId, const char* phase, bool occupied) {
  StaticJsonDocument<512> doc;  // Increased size for array and nested objects
  time_t now = time(nullptr);

  // Create an array with one object inside
  JsonArray arr = doc.to<JsonArray>();

  JsonObject obj = arr.createNestedObject();
  obj["slot_id"] = slotId;
  obj["vehicleid"] = vehicleId;
  obj["phase"] = phase;

  JsonObject data = obj.createNestedObject("data");
  data["status"] = occupied ? "occupied" : "vacant";
  data["timestamp"] = now;

  char buffer[512];
  serializeJson(doc, buffer);

  Serial.println("📤 Publishing to AWS IoT:");
  Serial.print("Topic: esp32/SmartParking/status\nPayload: ");
  Serial.println(buffer);

  if (mqttClient.connected()) {
    mqttClient.publish("esp32/SmartParking/status", buffer);
    Serial.println("✅ MQTT publish successful");
  } else {
    Serial.println("❌ MQTT not connected");
  }
}

void setup() {
  Serial.begin(115200);

  // Init SPIFFS
  if (!SPIFFS.begin(true)) {
    Serial.println("❌ SPIFFS mount failed");
    return;
  }

  // Connect to AWS IoT
  connectAWS();

  // Sensor/LED/Servo pin setup
  pinMode(irEntry, INPUT);
  pinMode(irSlot1, INPUT);
  pinMode(irSlot2, INPUT);
  pinMode(irExit, INPUT);
  pinMode(ledSlot1, OUTPUT);
  pinMode(ledSlot2, OUTPUT);

  // Attach servos
  servoEntry.setPeriodHertz(50);
  servoEntry.attach(servoEntryPin, 500, 2400);
  servoEntry.write(0);

  servoExit.setPeriodHertz(50);
  servoExit.attach(servoExitPin, 500, 2400);
  servoExit.write(0);

  digitalWrite(ledSlot1, LOW);
  digitalWrite(ledSlot2, LOW);
}

void loop() {
  if (!mqttClient.connected()) {
    connectAWS();
  }
  mqttClient.loop();

  // IR sensor readings
  int entryIR = digitalRead(irEntry);
  int exitIR  = digitalRead(irExit);
  int slot1IR = digitalRead(irSlot1);
  int slot2IR = digitalRead(irSlot2);

  // Entry gate control
  if (entryIR == LOW && !entryGateOpen) {
    Serial.println("🚗 Entry detected - opening gate");
    servoEntry.write(90);
    entryGateOpen = true;
  } else if (entryIR == HIGH && entryGateOpen) {
    Serial.println("🚪 Entry cleared - closing gate");
    servoEntry.write(0);
    entryGateOpen = false;
  }

  // Exit gate control
  if (exitIR == LOW && !exitGateOpen) {
    Serial.println("🚙 Exit detected - opening gate");
    servoExit.write(90);
    exitGateOpen = true;
  } else if (exitIR == HIGH && exitGateOpen) {
    Serial.println("🚪 Exit cleared - closing gate");
    servoExit.write(0);
    exitGateOpen = false;
  }

  // SLOT 1
  if (slot1IR == LOW && !slot1Occupied) {
    Serial.println("🔴 Slot 1 Occupied");
    digitalWrite(ledSlot1, HIGH);
    slot1Occupied = true;
    publishSlotStatus("slot1", "abc-123","entry",true);
  } else if (slot1IR == HIGH && slot1Occupied) {
    Serial.println("🟢 Slot 1 Vacant");
    digitalWrite(ledSlot1, LOW);
    slot1Occupied = false;
    publishSlotStatus("slot1", "abc-123","exit",false);
  }

  // SLOT 2
  if (slot2IR == LOW && !slot2Occupied) {
    Serial.println("🔴 Slot 2 Occupied");
    digitalWrite(ledSlot2, HIGH);
    slot2Occupied = true;
    publishSlotStatus("slot2", "abc-123","entry",true);
  } else if (slot2IR == HIGH && slot2Occupied) {
    Serial.println("🟢 Slot 2 Vacant");
    digitalWrite(ledSlot2, LOW);
    slot2Occupied = false;
    publishSlotStatus("slot2", "abc-123","exit",false);
  }

  delay(200);
}
