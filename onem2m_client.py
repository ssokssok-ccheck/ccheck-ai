# onem2m_client.py

import json
import uuid
import requests

from config import ONEM2M_CSE_BASE, ONEM2M_ORIGIN
from secrets import ONEM2M_API_KEY, ONEM2M_LECTURE_ID, ONEM2M_CREATOR_ID


def _post_content_instance(container_path, content):
    """
    oneM2M CSE의 container 밑에 contentInstance(cin)를 하나 생성한다.
    """

    url = f"{ONEM2M_CSE_BASE}{container_path}"

    headers = {
        "Accept": "application/json",
        "X-M2M-Origin": ONEM2M_ORIGIN,
        "X-M2M-RI": str(uuid.uuid4()),
        "Content-Type": "application/json;ty=4",
        "X-API-KEY": ONEM2M_API_KEY,
        "X-AUTH-CUSTOM-LECTURE": ONEM2M_LECTURE_ID,
        "X-AUTH-CUSTOM-CREATOR": ONEM2M_CREATOR_ID,
    }

    body = {
        "m2m:cin": {
            "cnf": "application/json",
            "con": json.dumps(content, ensure_ascii=False)
        }
    }

    try:
        response = requests.post(url, headers=headers, json=body, timeout=5)
    except requests.RequestException as e:
        print(f"[oneM2M] {container_path} 전송 실패 (연결 오류): {e}")
        return None

    if response.status_code not in (200, 201):
        print(f"[oneM2M] {container_path} 전송 실패: {response.status_code} {response.text}")
        return None

    print(f"[oneM2M] {container_path} 전송 성공")
    return response.json()


def send_classification_event(location, station_id, event):
    path = f"/ccheck/{location}/{station_id}/classificationLog"
    return _post_content_instance(path, event)


def send_bin_status(location, station_id, event):
    path = f"/ccheck/{location}/{station_id}/binStatusLog"
    return _post_content_instance(path, event)
