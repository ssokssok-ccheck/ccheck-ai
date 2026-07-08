# main_sensor_clip_test.py

import cv2
import json
from datetime import datetime

from arduino_serial import ArduinoSerial
from ai_classifier import classify_frame
from decision_logic import decide_disposal
from config import STATION_ID


SENSOR_PORT = "/dev/cu.usbmodem3CDC75484A642"  # Arduino A 실제 포트로 수정
BAUDRATE = 9600


def make_arduino_command(decision_result):
    if decision_result["decision"] == "AUTO_SORT":
        return {
            "command": "SORT",
            "targetBin": decision_result["targetBin"]
        }

    return {
        "command": "STOP",
        "targetBin": None
    }


def make_classification_event(ai_result, sensor_data, decision_result):
    return {
        "type": "classificationEvent",
        "stationId": STATION_ID,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

        "itemType": ai_result["itemType"],
        "itemName": ai_result["itemName"],

        "objectDetected": sensor_data["objectDetected"],
        "weight": sensor_data["weight"],
        "moisture": sensor_data["moisture"],
        "moistureValue": sensor_data["moistureValue"],

        "decision": decision_result["decision"],
        "targetBin": decision_result["targetBin"],
        "success": decision_result["success"]
    }


sensor_arduino = ArduinoSerial(SENSOR_PORT, BAUDRATE, name="Arduino A 센서")


camera_index = 0
cap = cv2.VideoCapture(camera_index)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    print("웹캠을 열 수 없습니다.")
    exit()

print("실행 중")
print("Arduino A에서 sensorData가 오면 자동으로 CLIP 분류합니다.")
print("Arduino B로는 아직 보내지 않고, command를 출력만 합니다.")
print("q: 종료")


while True:
    ret, frame = cap.read()

    if not ret:
        print("웹캠 프레임을 읽을 수 없습니다.")
        break

    cv2.imshow("Sensor + CLIP Test", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break

    # 1. Arduino A에서 sensorData 받기
    sensor_data = sensor_arduino.read_json()

    if sensor_data is None:
        continue

    if sensor_data.get("type") != "sensorData":
        continue

    if not sensor_data.get("objectDetected", False):
        print("물체 감지 안 됨")
        continue

    print("\n========== Arduino A에서 받은 sensorData ==========")
    print(json.dumps(sensor_data, ensure_ascii=False, indent=2))

    # 2. sensorData가 들어온 순간 현재 웹캠 화면으로 CLIP 실행
    print("\nCLIP 분류 중...")
    ai_result = classify_frame(frame)

    print("\n========== CLIP 결과 ==========")
    print(json.dumps(ai_result, ensure_ascii=False, indent=2))

    # 3. 품목 + 센서값으로 최종 판단
    decision_result = decide_disposal(
        item_type=ai_result["itemType"],
        weight=sensor_data["weight"],
        moisture=sensor_data["moisture"]
    )

    print("\n========== 판단 결과 ==========")
    print(json.dumps(decision_result, ensure_ascii=False, indent=2))

    # 4. Arduino B에 보낼 command를 만들되, 지금은 전송하지 않고 출력만 함
    arduino_command = make_arduino_command(decision_result)

    print("\n========== 나중에 Arduino B로 보낼 command ==========")
    print(json.dumps(arduino_command, ensure_ascii=False, indent=2))

    # 5. oneM2M 플랫폼에 보낼 classificationEvent 출력
    classification_event = make_classification_event(
        ai_result=ai_result,
        sensor_data=sensor_data,
        decision_result=decision_result
    )

    print("\n========== oneM2M 플랫폼에 보낼 classificationEvent ==========")
    print(json.dumps(classification_event, ensure_ascii=False, indent=2))
    print("====================================================\n")


cap.release()
cv2.destroyAllWindows()
sensor_arduino.close()