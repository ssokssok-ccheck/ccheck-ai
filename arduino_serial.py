# arduino_serial.py

import json
import serial
import time


class ArduinoSerial:
    def __init__(self, port, baudrate=9600, name="Arduino"):
        self.name = name
        self.ser = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2)
        print(f"{self.name} 연결 완료: {port}")

    def read_json(self):
        line = self.ser.readline().decode("utf-8", errors="ignore").strip()

        if not line:
            return None

        try:
            return json.loads(line)
        except json.JSONDecodeError:
            print(f"{self.name} JSON 파싱 실패:", line)
            return None

    def send_json(self, data):
        message = json.dumps(data, ensure_ascii=False) + "\n"
        self.ser.write(message.encode("utf-8"))
        print(f"{self.name}로 전송:", message.strip())

    def close(self):
        self.ser.close()