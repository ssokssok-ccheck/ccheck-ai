# main_test.py

import cv2
import json
from datetime import datetime

from config import STATION_ID
from ai_classifier import classify_frame
from decision_logic import decide_disposal


def get_fake_sensor_data(item_type):
    """
    아직 Arduino 연결 전이라 임시 sensorData를 넣는다.
    나중에는 Arduino에서 받은 JSON으로 교체한다.
    """

    if item_type == "PET_BOTTLE":
        return {
            "type": "sensorData",
            "objectDetected": True,
            "weight": 135.2,
            "moisture": False,
            "moistureValue": 120
        }

    if item_type == "CAN":
        return {
            "type": "sensorData",
            "objectDetected": True,
            "weight": 16.5,
            "moisture": False,
            "moistureValue": 100
        }

    if item_type == "PAPER_CUP":
        return {
            "type": "sensorData",
            "objectDetected": True,
            "weight": 12.0,
            "moisture": True,
            "moistureValue": 650
        }

    if item_type == "RECEIPT":
        return {
            "type": "sensorData",
            "objectDetected": True,
            "weight": 2.0,
            "moisture": False,
            "moistureValue": 100
        }

    return {
        "type": "sensorData",
        "objectDetected": True,
        "weight": 0,
        "moisture": False,
        "moistureValue": 0
    }


def make_arduino_command(decision_result):
    """
    PC → Arduino로 보낼 명령 JSON 생성
    """

    if decision_result["decision"] == "AUTO_SORT":
        return {
            "command": "SORT",
            "targetBin": decision_result["targetBin"]
        }

    return {
        "command": "STOP",
        "targetBin": None
    }


camera_index = 0
cap = cv2.VideoCapture(camera_index)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    print("웹캠을 열 수 없습니다. camera_index를 1 또는 2로 바꿔보세요.")
    exit()

print("실행 중")
print("스페이스바: CLIP 분류 + 판단 로직 테스트")
print("q: 종료")


while True:
    ret, frame = cap.read()

    if not ret:
        print("프레임을 읽을 수 없습니다.")
        break

    cv2.imshow("Sortree Main Test - Press SPACE", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

    if key == ord(" "):
        print("\nCLIP 분류 중...")

        # 1. CLIP으로 품목 판단
        ai_result = classify_frame(frame)

        # 2. Arduino에서 받았다고 가정한 sensorData
        sensor_data = get_fake_sensor_data(ai_result["itemType"])

        # 3. 품목 + 센서값으로 최종 판단
        decision_result = decide_disposal(
            item_type=ai_result["itemType"],
            weight=sensor_data["weight"],
            moisture=sensor_data["moisture"]
        )

        # 4. Arduino에 보낼 명령 생성
        arduino_command = make_arduino_command(decision_result)

        # 5. oneM2M 플랫폼에 보낼 classificationEvent 생성
        classification_event = {
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

        print("\n========== CLIP 결과 ==========")
        print(json.dumps(ai_result, ensure_ascii=False, indent=2))

        print("\n========== Arduino에서 받은 sensorData 가정 ==========")
        print(json.dumps(sensor_data, ensure_ascii=False, indent=2))

        print("\n========== Arduino에 보낼 command ==========")
        print(json.dumps(arduino_command, ensure_ascii=False, indent=2))

        print("\n========== oneM2M 플랫폼에 보낼 classificationEvent ==========")
        print(json.dumps(classification_event, ensure_ascii=False, indent=2))
        print("====================================================\n")


cap.release()
cv2.destroyAllWindows()