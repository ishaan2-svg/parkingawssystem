# Smart Parking System using AWS IoT

An intelligent parking system that utilizes **ESP32 microcontrollers**, **IR sensors**, and **AWS IoT Core** to manage real-time parking slot detection, QR-based entry/exit, and automated billing via a web dashboard.

---

## Features

- Real-time parking slot occupancy monitoring using IR sensors
- Entry detection via ESP32 + IR sensor at gate
- QR code generation for slot reservation
- Timer-based billing system (start/stop on entry/exit)
- Web dashboard showing:
  - Live slot status
  - QR codes for reserved slots
  - Duration-based charges
- Integration with **AWS IoT Core** for real-time communication
- DynamoDB backend for user and slot data

---

## Tech Stack

- **Frontend**: React + Tailwind CSS + Flowbite
- **Backend**: AWS Lambda, API Gateway
- **Database**: DynamoDB
- **Hardware**: ESP32 + IR Sensors + Servo Motor (Gate)
- **Cloud**: AWS IoT Core, MQTT

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/ishaan2-svg/parkingawssystem.git
cd parkingawssystem
```
2. Install Frontend Dependencies
```bash
Copy
Edit
cd frontend
npm install
npm run dev
```
3. AWS Setup
-Configure AWS IoT Core with Thing, Policy, and Certificate
-Set up DynamoDB tables:
--ParkingData with slot_id and vehicleid
-Deploy Lambda functions for:
--Slot update
--Payment generation
--QR creation

4. Hardware Setup
-ESP32 microcontroller
-IR sensors at gate and each slot
-Servo motor for gate control
-Wi-Fi enabled for MQTT communication to AWS IoT

5. Future Enhancements
-Payment gateway integration (UPI/Stripe)
-Admin dashboard with analytics
-SMS/Email alerts on slot expiration
