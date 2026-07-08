# serial_test.py

from arduino_serial import ArduinoSerial

PORT = "/dev/cu.usbmodem3CDC75484A642"  

arduino = ArduinoSerial(PORT, 9600)

while True:
    data = arduino.read_json()

    if data is None:
        continue

    print("Arduino에서 받은 값:", data)

    if data.get("type") == "sensorData":
        command = {
            "command": "SORT",
            "targetBin": "plastic"
        }

        arduino.send_json(command)