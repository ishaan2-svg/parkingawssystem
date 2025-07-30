#ifndef UTILS_H
#define UTILS_H

#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "certs.h"

// AWS WiFi Credentials
#define WIFI_SSID       "Note 10+"
#define WIFI_PASSWORD   "isar0510"
#define THINGNAME       "SmartParkingESP32"
#define AWS_IOT_ENDPOINT "a3oq41aouks5wc-ats.iot.ap-south-1.amazonaws.com"

#define AWS_IOT_PUBLISH_TOPIC   "esp32/SmartParking/status"
#define AWS_IOT_SUBSCRIBE_TOPIC "esp32/SmartParking/commands"

// Declare globally used clients
extern WiFiClientSecure net;
extern PubSubClient mqttClient;

// Functions
void connectAWS();
void publishMessage(int metricsValue);

#endif
