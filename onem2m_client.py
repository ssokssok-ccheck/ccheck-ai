# onem2m_client.py

import json
import uuid

import requests

from config import ONEM2M_CSE_BASE, ONEM2M_ORIGIN
from onem2m_secrets import (
    ONEM2M_API_KEY,
    ONEM2M_LECTURE_ID,
    ONEM2M_CREATOR_ID,
)


def _post_content_instance(container_path, content):
    """
    oneM2M Container 아래에 ContentInstance(CIN)를 생성한다.

    성공 시 서버 응답 JSON을 반환하고,
    실패 시 None을 반환한다.
    """

    # 주소 사이에 /가 중복되거나 빠지지 않도록 정리한다.
    url = (
        f"{ONEM2M_CSE_BASE.rstrip('/')}/"
        f"{container_path.lstrip('/')}"
    )

    request_id = str(uuid.uuid4())

    headers = {
        "Accept": "application/json",
        "X-M2M-Origin": ONEM2M_ORIGIN,
        "X-M2M-RI": request_id,
        "Content-Type": "application/json;ty=4",
        "X-API-KEY": ONEM2M_API_KEY,
        "X-AUTH-CUSTOM-LECTURE": ONEM2M_LECTURE_ID,
        "X-AUTH-CUSTOM-CREATOR": ONEM2M_CREATOR_ID,
    }

    # content를 JSON 문자열로 변환하지 않고 객체 그대로 저장한다.
    body = {
        "m2m:cin": {
            "cnf": "application/json",
            "con": content,
        }
    }

    # API Key 등 비밀값은 로그에 출력하지 않는다.
    print("=" * 60)
    print(f"[oneM2M] POST URL: {url}")
    print(f"[oneM2M] Request ID: {request_id}")
    print(
        "[oneM2M] Request Body:",
        json.dumps(
            body,
            ensure_ascii=False,
            default=str,
        ),
    )

    try:
        response = requests.post(
            url,
            headers=headers,
            json=body,
            timeout=10,
        )
    except requests.Timeout:
        print("[oneM2M] 전송 실패: 요청 시간 초과")
        return None
    except requests.ConnectionError as error:
        print(f"[oneM2M] 전송 실패: 연결 오류 - {error}")
        return None
    except requests.RequestException as error:
        print(f"[oneM2M] 전송 실패: 요청 오류 - {error}")
        return None

    print(f"[oneM2M] Response Status: {response.status_code}")
    print(f"[oneM2M] Response Body: {response.text}")

    if response.status_code not in (200, 201):
        print(
            f"[oneM2M] {container_path} 전송 실패: "
            f"HTTP {response.status_code}"
        )
        return None

    print(f"[oneM2M] {container_path} 전송 성공")

    try:
        return response.json()
    except ValueError:
        return {
            "status_code": response.status_code,
            "text": response.text,
        }

def send_classification_event(location, station_id, event):
    path = f"/CCheck/donggukUniv/{station_id}/classificationLog"
    return _post_content_instance(path, event)


def send_bin_status(location, station_id, event):
    path = f"/CCheck/donggukUniv/{station_id}/binStatusLog"
    return _post_content_instance(path, event)


if __name__ == "__main__":
    # 파일을 직접 실행했을 때만 동작하는 전송 테스트
    test_event = {
        "classification": "test-from-python",
    }

    result = send_classification_event(
        location="donggukUniv",
        station_id="station01",
        event=test_event,
    )

    if result is None:
        print("[oneM2M] 테스트 최종 결과: 실패")
    else:
        print("[oneM2M] 테스트 최종 결과: 성공")
        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
            )
        )