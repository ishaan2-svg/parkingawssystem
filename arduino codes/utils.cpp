#include "utils.h"
#include <WiFi.h>

// Create the clients
WiFiClientSecure net;
PubSubClient mqttClient(net);

void messageHandler(char* topic, byte* payload, unsigned int length) {
  Serial.print("📩 Incoming message on topic: ");
  Serial.println(topic);

  String message;
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  Serial.print("📨 Payload: ");
  Serial.println(message);

  StaticJsonDocument<200> doc;
  DeserializationError error = deserializeJson(doc, message);

  if (!error) {
    const char* cmd = doc["message"];
    Serial.print("🧠 Command: ");
    Serial.println(cmd);
    // Do something with the command if needed
  }
}

void connectAWS() {
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ WiFi connected!");

  net.setCACert(AWS_CERT_CA);
  net.setCertificate(AWS_CERT_CRT);
  net.setPrivateKey(AWS_CERT_PRIVATE);

  mqttClient.setServer(AWS_IOT_ENDPOINT, 8883);
  mqttClient.setCallback(messageHandler);

  Serial.print("🔌 Connecting to AWS IoT");
  while (!mqttClient.connected()) {
    if (mqttClient.connect(THINGNAME)) {
      Serial.println("\n✅ Connected to AWS IoT");
    } else {
      Serial.print(".");
      delay(1000);
    }
  }

  mqttClient.subscribe(AWS_IOT_SUBSCRIBE_TOPIC);
}

void publishMessage(int value) {
  StaticJsonDocument<200> doc;
  doc["metrics"] = value;

  char jsonBuffer[256];
  serializeJson(doc, jsonBuffer);
  mqttClient.publish(AWS_IOT_PUBLISH_TOPIC, jsonBuffer);

  Serial.print("📤 Published test metric: ");
  Serial.println(jsonBuffer);
}
