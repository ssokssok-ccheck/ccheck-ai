
def decide_disposal(item_type, weight, moisture):
    """
    CLIP 품목 결과 + Arduino 센서값을 이용해서
    자동분류할지, 안내만 할지 결정한다.
    """

    if item_type == "PET_BOTTLE":
        if moisture:
            return {
                "decision": "GUIDE_ONLY",
                "targetBin": None,
                "success": False
            }

        return {
            "decision": "AUTO_SORT",
            "targetBin": "plastic",
            "success": True
        }

    if item_type == "CAN":
        if moisture:
            return {
                "decision": "GUIDE_ONLY",
                "targetBin": None,
                "success": False
            }

        return {
            "decision": "AUTO_SORT",
            "targetBin": "can",
            "success": True
        }

    if item_type == "PAPER_CUP":
        if moisture:
            return {
                "decision": "GUIDE_ONLY",
                "targetBin": None,
                "success": False
            }

        return {
            "decision": "AUTO_SORT",
            "targetBin": "paper",
            "success": True
        }

    if item_type == "RECEIPT":
        return {
            "decision": "AUTO_SORT",
            "targetBin": "general",
            "success": True
        }

    # 유리병, 깨진 유리, 알 수 없음 등
    return {
        "decision": "GUIDE_ONLY",
        "targetBin": None,
        "success": False
    }