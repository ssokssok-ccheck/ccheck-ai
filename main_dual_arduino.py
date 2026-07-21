# main_dual_arduino.py

import cv2
import json
import time
import uuid
from datetime import datetime

from arduino_serial import ArduinoSerial
from ai_classifier import classify_frame
from decision_logic import decide_disposal
from config import STATION_ID, LOCATION, ITEM_TYPE_TO_CATEGORY, ITEM_TYPE_AVG_WEIGHT
import onem2m_client


SENSOR_PORT = "COM5"  # Arduino A: sensorData 보내는 아두이노    # Arduino A: sensorData 보내는 아두이노
CONTROL_PORT = "COM6"   # Arduino B: command 받기 + binStatus 보내는 아두이노

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


def make_event_id():
    return f"evt_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"


def make_classification_event(ai_result, sensor_data, decision_result):
    return {
        "event_id": make_event_id(),
        "device_id": STATION_ID,
        "location": LOCATION,

        "item": ai_result["itemName"],
        "category": ITEM_TYPE_TO_CATEGORY[ai_result["itemType"]],
        "confidence": ai_result["aiScore"],

        # 품목별 평균 무게로 oneM2M에 기록한다.
        "weight_g": ITEM_TYPE_AVG_WEIGHT.get(ai_result["itemType"], sensor_data["weight"]),
        "is_wet": sensor_data["moisture"],
        "has_content": sensor_data["moisture"],

        "decision": decision_result["targetBin"],
        "status": "success" if decision_result["success"] else "guide_only",

        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def make_bin_status_event(bin_status_data):
    return {
        "device_id": STATION_ID,
        "location": LOCATION,
        "bin_fill": bin_status_data["binFillLevels"],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def wait_for_bin_status(control_arduino, timeout_sec=10):
    """
    Arduino B에 SORT/STOP 명령을 보낸 후,
    B가 보내는 binStatus를 기다린다.
    timeout_sec 안에 안 오면 None 반환.
    """

    start_time = time.time()

    while time.time() - start_time < timeout_sec:
        data = control_arduino.read_json()

        if data is None:
            continue

        if data.get("type") == "binStatus":
            return data

        # 혹시 B가 다른 JSON을 보내면 무시
        print("Arduino B에서 binStatus가 아닌 데이터 수신:")
        print(json.dumps(data, ensure_ascii=False, indent=2))

    return None


sensor_arduino = ArduinoSerial(SENSOR_PORT, BAUDRATE, name="Arduino A 센서")
control_arduino = ArduinoSerial(CONTROL_PORT, BAUDRATE, name="Arduino B 제어")


camera_index = 1
cap = cv2.VideoCapture(camera_index)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    print("웹캠을 열 수 없습니다.")
    sensor_arduino.close()
    control_arduino.close()
    exit()

print("실행 중")
print("흐름: sensorData 수신 → CLIP 분류 → 판단 → Arduino B 명령 전송 → classificationEvent 출력 → binStatus 수신/출력")
print("q: 종료")


while True:
    ret, frame = cap.read()

    if not ret:
        print("웹캠 프레임을 읽을 수 없습니다.")
        break

    cv2.imshow("Sortree Dual Arduino", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break

    # 1. Arduino A에서 sensorData 받기
    sensor_data = sensor_arduino.read_json()

    if sensor_data is None:
        continue

    # sensorData 타입만 처리
    if sensor_data.get("type") != "sensorData":
        continue

    # 물체가 감지되지 않았으면 처리 안 함
    if not sensor_data.get("objectDetected", False):
        print("물체 감지 안 됨")
        continue

    print("\n========== 1. Arduino A에서 받은 sensorData ==========")
    print(json.dumps(sensor_data, ensure_ascii=False, indent=2))

    # 2. CLIP으로 현재 웹캠 화면 분류
    print("\nCLIP 분류 중...")
    ai_result = classify_frame(frame)

    print("\n========== 2. CLIP 결과 ==========")
    print(json.dumps(ai_result, ensure_ascii=False, indent=2))

    # 3. 품목 + 센서값으로 최종 판단
    decision_result = decide_disposal(
        item_type=ai_result["itemType"],
        weight=sensor_data["weight"],
        moisture=sensor_data["moisture"]
    )

    print("\n========== 3. 판단 결과 ==========")
    print(json.dumps(decision_result, ensure_ascii=False, indent=2))

    # 4. Arduino B에 보낼 명령 생성
    arduino_command = make_arduino_command(decision_result)

    # 5. Arduino B로 명령 전송
    control_arduino.send_json(arduino_command)

    print("\n========== 4. Arduino B로 보낸 command ==========")
    print(json.dumps(arduino_command, ensure_ascii=False, indent=2))

    # 6. oneM2M 플랫폼에 보낼 classificationEvent 생성 및 전송
    classification_event = make_classification_event(
        ai_result=ai_result,
        sensor_data=sensor_data,
        decision_result=decision_result
    )

    print("\n========== 5. oneM2M 플랫폼에 보낼 classificationEvent ==========")
    print(json.dumps(classification_event, ensure_ascii=False, indent=2))

    onem2m_client.send_classification_event(LOCATION, STATION_ID, classification_event)

    # 7. Arduino B가 동작 후 보내는 binStatus 기다리기
    print("\nArduino B에서 binStatus 기다리는 중...")

    bin_status_data = wait_for_bin_status(control_arduino, timeout_sec=10)

    if bin_status_data is None:
        print("\n========== 6. binStatus 수신 실패 ==========")
        print("10초 안에 Arduino B에서 binStatus가 오지 않았습니다.")
        print("Arduino B가 동작 완료 후 binStatus JSON을 보내는지 확인하세요.")
        print("====================================================\n")
        continue

    bin_status_event = make_bin_status_event(bin_status_data)

    print("\n========== 6. oneM2M 플랫폼에 보낼 binStatus ==========")
    print(json.dumps(bin_status_event, ensure_ascii=False, indent=2))

    onem2m_client.send_bin_status(LOCATION, STATION_ID, bin_status_event)
    print("====================================================\n")


cap.release()
cv2.destroyAllWindows()
sensor_arduino.close()
control_arduino.close()