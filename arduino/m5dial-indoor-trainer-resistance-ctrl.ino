/*
Peloton style controller for your smart trainer.
*/

#include "M5Dial.h"
#include "BLEDevice.h"

// FTMS
static BLEUUID        ftms_UUID("00001826-0000-1000-8000-00805f9b34fb");
static BLEUUID     ftms_cp_UUID("00002ad9-0000-1000-8000-00805f9b34fb");
static BLEUUID ftms_status_UUID("00002ada-0000-1000-8000-00805f9b34fb");

static boolean doConnect = false;
static boolean connected = false;
static boolean doScan = false;
static BLERemoteCharacteristic* ftms_cp_p;
static BLERemoteCharacteristic* ftms_status_p;
static BLEAdvertisedDevice* device_p;
bool send_payload = false;
uint8_t payload[] = {0, 0};
unsigned long previousMillis = 0;
unsigned long rotaryDelay = 1000UL;

static void notifyCallback(
  BLERemoteCharacteristic* pBLERemoteCharacteristic,
  uint8_t* pData,
  size_t length,
  bool isNotify) {

    if (pBLERemoteCharacteristic == ftms_status_p) {
      uint8_t op_code = pData[0];
      uint8_t value = pData[1];
      Serial.printf("<- [ftms_status] op_code: %d, value: %d\n", op_code, value);
    } else {
      Serial.printf("<- [ftms_cp] response_code: %d, op_code: %d, value: %d\n", 
                  pData[0],
                  pData[1],
                  pData[2]);
    }
}

class MyClientCallback : public BLEClientCallbacks {
  void onConnect(BLEClient* pclient) {
  }

  void onDisconnect(BLEClient* pclient) {
    connected = false;
    Serial.println("[info] disconnected");
  }
};

bool connectToServer() {
    Serial.printf("[info] connecting... %s\n", device_p->getAddress().toString().c_str());

    BLEClient*  pClient  = BLEDevice::createClient();
    pClient->setClientCallbacks(new MyClientCallback());
    pClient->connect(device_p); 
    pClient->setMTU(517);
  
    BLERemoteService* ftms_service_p = pClient->getService(ftms_UUID);
    if (ftms_service_p == nullptr) {
      Serial.printf("[error] no service UUID: %s", ftms_UUID.toString().c_str());
      pClient->disconnect();
      return false;
    }

    ftms_cp_p = ftms_service_p->getCharacteristic(ftms_cp_UUID);
    if (ftms_cp_p == nullptr) {
      Serial.printf("[error] no characteristic UUID: %s", ftms_cp_UUID.toString().c_str());
      pClient->disconnect();
      return false;
    }
    ftms_status_p = ftms_service_p->getCharacteristic(ftms_status_UUID);
    if (ftms_status_p == nullptr) {
      Serial.printf("[error] no characteristic UUID: %s", ftms_status_UUID.toString().c_str());
      pClient->disconnect();
      return false;
    }

    if(ftms_cp_p->canIndicate())
      ftms_cp_p->registerForNotify(notifyCallback, false);

    if(ftms_status_p->canNotify())
      ftms_status_p->registerForNotify(notifyCallback);

    connected = true;
    return true;
}

class MyAdvertisedDeviceCallbacks: public BLEAdvertisedDeviceCallbacks {
  void onResult(BLEAdvertisedDevice advertisedDevice) {
    if (advertisedDevice.haveServiceUUID() && advertisedDevice.isAdvertisingService(ftms_UUID)) {
      Serial.printf("[device]: %s\n", advertisedDevice.toString().c_str());
      BLEDevice::getScan()->stop();
      device_p = new BLEAdvertisedDevice(advertisedDevice);
      doConnect = true;
      doScan = true;
    }
  }
};

void setup() {
    auto cfg = M5.config();
    M5Dial.begin(cfg, true, false);
    M5Dial.Display.setTextColor(WHITE);
    M5Dial.Display.setTextDatum(middle_center);
    M5Dial.Display.setTextFont(&fonts::Roboto_Thin_24);
    M5Dial.Display.setTextSize(2);

    Serial.begin(115200);
    Serial.println("[info] Scanning for the nearest device with FTMS...");

    BLEDevice::init("");
    BLEScan* pBLEScan = BLEDevice::getScan();
    pBLEScan->setAdvertisedDeviceCallbacks(new MyAdvertisedDeviceCallbacks());
    pBLEScan->setInterval(1349);
    pBLEScan->setWindow(449);
    pBLEScan->setActiveScan(true);
    pBLEScan->start(5, false);
}

long oldPosition = 0;

void loop() {
  M5Dial.update();

  if (doConnect == true) {
    if (!connectToServer()) {
      Serial.println("[error] failed to connect to the server.");
    }
    doConnect = false;
  }
  if (connected) {   
    if (send_payload && (millis() - previousMillis) > rotaryDelay) {
      Serial.printf("-> [ftms_cp] %d %d\n", payload[0], payload[1]);
      ftms_cp_p->writeValue(payload, 2);
      send_payload = false;
    }

    int newPosition = M5Dial.Encoder.read();
    if (newPosition < 0) {
      M5Dial.Encoder.write(0);
      return;
    }
    else if (newPosition > 100) {
      M5Dial.Encoder.write(100);
      return;
    }

    if (newPosition != oldPosition) {
        previousMillis = millis();
        M5Dial.Speaker.tone(8000, 20);
        M5Dial.Display.clear();
        oldPosition = newPosition;
        
        M5Dial.Display.setTextSize(2);
        M5Dial.Display.drawString(String(newPosition) + "%",
                                  M5Dial.Display.width() / 2,
                                  M5Dial.Display.height() / 2,
                                  &fonts::FreeSansBoldOblique24pt7b);
        M5Dial.Display.setTextSize(1);
        M5Dial.Display.drawString("PELOTON-CTRL",
                                  M5Dial.Display.width() / 2,
                                  170);
        M5Dial.Display.drawString(String(device_p->getName().c_str()) + " [" + String(device_p->getRSSI()) + "]",
                                  M5Dial.Display.width() / 2,
                                  190,
                                  &fonts::Font0);

        payload[0] = 4;
        payload[1] = newPosition;
        send_payload = true;
    }
  } else if(doScan) {
    BLEDevice::getScan()->start(5);
    delay(5000);
  }
}