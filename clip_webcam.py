import cv2
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel


# 1. CLIP 모델 이름
MODEL_NAME = "openai/clip-vit-base-patch32"


# 2. 후보 라벨과 내부 itemType 매핑
label_to_item_type = {
    "a photo of a plastic bottle": "PET_BOTTLE",
    "a photo of a transparent plastic water bottle": "PET_BOTTLE",
    "a photo of an empty plastic bottle": "PET_BOTTLE",

    "a photo of an aluminum can": "CAN",
    "a photo of a soda can": "CAN",
    "a photo of a beverage can": "CAN",

    "a photo of a paper cup": "PAPER_CUP",
    "a photo of a disposable paper cup": "PAPER_CUP",
    "a photo of a white paper cup": "PAPER_CUP",

    "a photo of a receipt": "RECEIPT",
    "a photo of a paper receipt": "RECEIPT",
    "a photo of a printed receipt": "RECEIPT",

    "a photo of a glass bottle": "GLASS_BOTTLE",
    "a photo of broken glass": "BROKEN_GLASS",
    "a photo of unknown trash": "UNKNOWN"
}

item_type_to_korean = {
    "PET_BOTTLE": "페트병",
    "CAN": "캔",
    "PAPER_CUP": "종이컵",
    "RECEIPT": "영수증",
    "GLASS_BOTTLE": "유리병",
    "BROKEN_GLASS": "깨진 유리",
    "UNKNOWN": "알 수 없음"
}

candidate_labels = list(label_to_item_type.keys())


# 3. CLIP 모델 로딩
print("CLIP 모델 로딩 중입니다. 처음 실행할 때는 시간이 걸릴 수 있어요.")

model = CLIPModel.from_pretrained(MODEL_NAME)
processor = CLIPProcessor.from_pretrained(MODEL_NAME)

model.eval()

print("CLIP 모델 로딩 완료")


# 4. 웹캠 열기
camera_index = 0
cap = cv2.VideoCapture(camera_index)

if not cap.isOpened():
    print("웹캠을 열 수 없습니다.")
    print("camera_index를 1 또는 2로 바꿔보세요.")
    exit()

print("웹캠 실행 중")
print("스페이스바: 현재 화면 캡처 후 CLIP 분류")
print("q: 종료")


while True:
    ret, frame = cap.read()

    if not ret:
        print("프레임을 읽을 수 없습니다.")
        break

    cv2.imshow("Sortree CLIP Webcam - Press SPACE", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

    if key == ord(" "):
        # OpenCV는 BGR이라 RGB로 변환
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb_frame)

        # CLIP 입력 만들기
        inputs = processor(
            text=candidate_labels,
            images=image,
            return_tensors="pt",
            padding=True
        )

        # 추론
        with torch.no_grad():
            outputs = model(**inputs)
            logits_per_image = outputs.logits_per_image
            probs = logits_per_image.softmax(dim=1)

        best_idx = probs.argmax().item()
        best_label = candidate_labels[best_idx]
        best_score = probs[0][best_idx].item()

        item_type = label_to_item_type[best_label]
        item_name = item_type_to_korean[item_type]

        print("\n==============================")
        print("CLIP 분류 결과")
        print("==============================")
        print(f"가장 가까운 라벨: {best_label}")
        print(f"itemType: {item_type}")
        print(f"한글 품목명: {item_name}")
        print(f"점수: {best_score:.4f}")

        print("\n전체 후보 점수:")
        for label, score in zip(candidate_labels, probs[0]):
            print(f"{label}: {score.item():.4f}")

        print("==============================\n")


cap.release()
cv2.destroyAllWindows()