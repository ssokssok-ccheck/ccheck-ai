
STATION_ID = "station01"
LOCATION = "dongguk_univ"

PET_BOTTLE_WEIGHT_LIMIT = 70  # g, 실제 테스트 후 수정
CAN_WEIGHT_LIMIT = 60         # g, 실제 테스트 후 수정

# oneM2M (Mobius) 설정
ONEM2M_CSE_BASE = "https://onem2m.iotcoss.ac.kr/Mobius"
ONEM2M_ORIGIN = "ccheck"

ITEM_NAME_KO = {
    "PET_BOTTLE": "페트병",
    "CAN": "캔",
    "PAPER_CUP": "종이컵",
    "RECEIPT": "영수증",
    "GLASS_BOTTLE": "유리병",
    "BROKEN_GLASS": "깨진 유리",
    "UNKNOWN": "알 수 없음"
}

# itemType -> 재질 분류 (oneM2M classificationEvent의 category 필드)
ITEM_TYPE_TO_CATEGORY = {
    "PET_BOTTLE": "plastic",
    "CAN": "can",
    "PAPER_CUP": "paper",
    "RECEIPT": "general",
    "GLASS_BOTTLE": "glass",
    "BROKEN_GLASS": "glass",
    "UNKNOWN": "general"
}