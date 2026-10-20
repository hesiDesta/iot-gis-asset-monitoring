/*
 * Node IoT aset (ESP32) - kirim suhu, getaran, dan baterai ke server via HTTP.
 * Sensor: DS18B20 (suhu, pin 4) + MPU6050 (getaran, I2C) + pembagi tegangan baterai (pin 34).
 * Library: OneWire, DallasTemperature, Adafruit MPU6050, ArduinoJson.
 * Lokasi aset tetap (dicatat saat instalasi), jadi tidak perlu modul GPS.
 */
#include <WiFi.h>
#include <HTTPClient.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <ArduinoJson.h>

const char* WIFI_SSID = "GANTI_SSID";
const char* WIFI_PASS = "GANTI_PASSWORD";
const char* SERVER_URL = "http://192.168.1.10:5000/api/telemetry";  // IP komputer server
const char* ASSET_ID = "PMP-01";                                     // sesuai data/assets.csv
const unsigned long INTERVAL_MS = 10000;

OneWire oneWire(4);
DallasTemperature tempSensor(&oneWire);
Adafruit_MPU6050 mpu;

float readVibration() {
  // Estimasi sederhana: besar percepatan dikurangi gravitasi, sebagai proxy getaran
  sensors_event_t a, g, t;
  mpu.getEvent(&a, &g, &t);
  float mag = sqrt(a.acceleration.x * a.acceleration.x +
                   a.acceleration.y * a.acceleration.y +
                   a.acceleration.z * a.acceleration.z);
  return fabs(mag - 9.81);
}

float readBatteryPercent() {
  int raw = analogRead(34);                 // 0..4095
  float volt = raw / 4095.0 * 3.3 * 2.0;    // pembagi tegangan 1:2
  float pct = (volt - 3.3) / (4.2 - 3.3) * 100.0;  // Li-ion 3.3V..4.2V
  return constrain(pct, 0, 100);
}

void connectWifi() {
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  Serial.println("\nWiFi terhubung");
}

void setup() {
  Serial.begin(115200);
  tempSensor.begin();
  Wire.begin();
  if (!mpu.begin()) { Serial.println("MPU6050 tidak ditemukan"); while (true) delay(1000); }
  connectWifi();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) connectWifi();

  tempSensor.requestTemperatures();
  StaticJsonDocument<200> doc;
  doc["asset_id"] = ASSET_ID;
  doc["temperature"] = tempSensor.getTempCByIndex(0);
  doc["vibration"] = readVibration();
  doc["battery"] = readBatteryPercent();

  String body;
  serializeJson(doc, body);

  HTTPClient http;
  http.begin(SERVER_URL);
  http.addHeader("Content-Type", "application/json");
  int code = http.POST(body);
  Serial.printf("POST %s -> %d\n", body.c_str(), code);
  http.end();

  delay(INTERVAL_MS);
}
