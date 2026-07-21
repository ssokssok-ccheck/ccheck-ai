import cv2
import torch
import torch.nn.functional as F
from PIL import Image
from transformers import CLIPModel, CLIPProcessor


MODEL_NAME = "openai/clip-vit-base-patch32"

# 실제로 인식할 품목만 둡니다. 클래스마다 프롬프트 수를 동일하게 유지해
# 특정 클래스가 프롬프트 개수 때문에 유리해지는 현상을 막습니다.
CLASS_PROMPTS = {
    "PINK_TOOTHBRUSH": [
        "a photo of a pink manual toothbrush",
        "a close-up photo of a pink toothbrush with bristles",
        "a single pink toothbrush on a plain background",
    ],
    "RED_COKE_CAN": [
        "a photo of a red Coca-Cola aluminum can",
        "a red Coke soda can with a white logo",
        "a single red Coca-Cola beverage can",
    ],
    "PET_BOTTLE": [
        "a photo of a transparent PET plastic bottle",
        "a clear plastic water bottle",
        "an empty transparent plastic beverage bottle",
    ],
    "SEOUL_MILK_CARTON": [
        "a photo of a white Seoul Milk carton",
        "a Korean Seoul Milk paper carton package",
        "a white milk carton with Korean writing",
    ],
    "PAPER_CUP": [
        "a photo of a disposable paper cup",
        "a single white paper cup",
        "an empty paper drinking cup",
    ],
}

ITEM_NAMES = {
    "PINK_TOOTHBRUSH": "핑크색 칫솔",
    "RED_COKE_CAN": "코카콜라 빨간 캔",
    "PET_BOTTLE": "페트병",
    "SEOUL_MILK_CARTON": "서울우유 우유팩",
    "PAPER_CUP": "종이컵",
    "UNKNOWN": "알 수 없음",
}

# 먼저 이 값으로 시작한 뒤 실제 카메라/조명에서 조정하세요.
# MIN_SIMILARITY를 올리면 UNKNOWN이 늘고, 내리면 인식 품목이 늘어납니다.
MIN_SIMILARITY = 0.245
# 1위와 2위가 비슷하면 애매한 물체이므로 UNKNOWN 처리합니다.
MIN_MARGIN = 0.012


device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"CLIP 모델 로딩 중 ({device})...")
model = CLIPModel.from_pretrained(MODEL_NAME).to(device)
processor = CLIPProcessor.from_pretrained(MODEL_NAME)
model.eval()


def build_class_features():
    """각 클래스의 여러 문장 임베딩을 평균내 하나의 대표 벡터로 만듭니다."""
    class_names = list(CLASS_PROMPTS)
    features = []

    with torch.no_grad():
        for class_name in class_names:
            text_inputs = processor(
                text=CLASS_PROMPTS[class_name],
                return_tensors="pt",
                padding=True,
            ).to(device)
            text_features = model.get_text_features(**text_inputs)
            text_features = F.normalize(text_features, dim=-1)
            prototype = F.normalize(text_features.mean(dim=0), dim=-1)
            features.append(prototype)

    return class_names, torch.stack(features)


CLASS_NAMES, CLASS_FEATURES = build_class_features()
print("CLIP 모델 로딩 완료")


def classify(image):
    image_inputs = processor(images=image, return_tensors="pt").to(device)

    with torch.no_grad():
        image_features = model.get_image_features(**image_inputs)
        image_features = F.normalize(image_features, dim=-1)
        similarities = image_features @ CLASS_FEATURES.T

    scores = similarities[0]
    top_scores, top_indices = torch.topk(scores, k=min(2, len(CLASS_NAMES)))
    best_score = top_scores[0].item()
    second_score = top_scores[1].item() if len(top_scores) > 1 else -1.0
    margin = best_score - second_score
    best_type = CLASS_NAMES[top_indices[0].item()]

    if best_score < MIN_SIMILARITY or margin < MIN_MARGIN:
        item_type = "UNKNOWN"
    else:
        item_type = best_type

    ranking = sorted(
        zip(CLASS_NAMES, scores.tolist()), key=lambda pair: pair[1], reverse=True
    )
    return item_type, best_type, best_score, margin, ranking


camera_index = 1
cap = cv2.VideoCapture(camera_index)
if not cap.isOpened():
    raise SystemExit("웹캠을 열 수 없습니다. camera_index를 0, 1 또는 2로 바꿔보세요.")

print("웹캠 실행 중 - SPACE: 분류, q: 종료")
last_result_text = "Press SPACE to classify"

while True:
    ret, frame = cap.read()
    if not ret:
        print("프레임을 읽을 수 없습니다.")
        break

    display_frame = frame.copy()
    cv2.putText(
        display_frame, last_result_text, (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2,
    )
    cv2.imshow("Sortree CLIP Webcam - Press SPACE", display_frame)
    key = cv2.waitKey(30) & 0xFF

    if key == ord("q"):
        break

    if key == ord(" "):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb_frame)
        item_type, nearest_type, score, margin, ranking = classify(image)
        last_result_text = f"{item_type} sim={score:.3f} margin={margin:.3f}"

        print("\n==============================")
        print(f"최종 결과: {item_type} ({ITEM_NAMES[item_type]})")
        print(f"가장 가까운 품목: {nearest_type}")
        print(f"유사도: {score:.4f} / 1·2위 차이: {margin:.4f}")
        print("품목별 유사도:")
        for class_name, class_score in ranking:
            print(f"  {class_name}: {class_score:.4f}")
        print("==============================\n")

cap.release()
cv2.destroyAllWindows()
