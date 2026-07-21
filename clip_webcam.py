import cv2
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel


# 1. CLIP 모델 이름
MODEL_NAME = "openai/clip-vit-base-patch32"


# 2. 후보 라벨과 내부 itemType 매핑
label_to_item_type = {
    # 페트병
    "a photo of a plastic bottle": "PET_BOTTLE",
    "a photo of a transparent plastic water bottle": "PET_BOTTLE",
    "a photo of an empty plastic bottle": "PET_BOTTLE",

    # 캔
    "a photo of an aluminum can": "CAN",
    "a photo of a soda can": "CAN",
    "a photo of a beverage can": "CAN",

    # 종이컵
    "a photo of a paper cup": "PAPER_CUP",
    "a photo of a disposable paper cup": "PAPER_CUP",
    "a photo of a white paper cup": "PAPER_CUP",

    # 영수증
    "a photo of a receipt": "RECEIPT",
    "a photo of a paper receipt": "RECEIPT",
    "a photo of a printed receipt": "RECEIPT",

    # 일반 칫솔
    "a photo of a toothbrush": "TOOTHBRUSH",
    "a photo of a used toothbrush": "TOOTHBRUSH",
    "a photo of a plastic toothbrush": "TOOTHBRUSH",
    "a photo of a toothbrush on a table": "TOOTHBRUSH",
    "a photo of a bathroom toothbrush": "TOOTHBRUSH",
    "a photo of a toothbrush handle": "TOOTHBRUSH",
    "a photo of toothbrush bristles": "TOOTHBRUSH",
    "a close-up photo of a toothbrush": "TOOTHBRUSH",

    # 초록색 칫솔
    "a photo of a green toothbrush": "TOOTHBRUSH",
    "a photo of a green and white toothbrush": "TOOTHBRUSH",

    # 파란색·흰색 칫솔
    "a photo of a toothbrush with a white handle": "TOOTHBRUSH",
    "a photo of a toothbrush with blue bristles": "TOOTHBRUSH",
    "a photo of a toothbrush with a white handle and blue bristles": "TOOTHBRUSH",
    "a photo of a white toothbrush with blue bristles": "TOOTHBRUSH",
    "a close-up photo of blue toothbrush bristles": "TOOTHBRUSH",
    "a photo of a blue and white toothbrush": "TOOTHBRUSH",

    # 분홍색 칫솔
    "a photo of a pink toothbrush": "TOOTHBRUSH",
    "a photo of a light pink toothbrush": "TOOTHBRUSH",
    "a photo of a bright pink toothbrush": "TOOTHBRUSH",
    "a photo of a pale pink toothbrush": "TOOTHBRUSH",
    "a photo of a pink and white toothbrush": "TOOTHBRUSH",
    "a photo of a white and pink toothbrush": "TOOTHBRUSH",
    "a photo of a toothbrush with a pink handle": "TOOTHBRUSH",
    "a photo of a toothbrush with a light pink handle": "TOOTHBRUSH",
    "a photo of a pink plastic toothbrush": "TOOTHBRUSH",
    "a photo of a pink toothbrush with white bristles": "TOOTHBRUSH",
    "a photo of a pink toothbrush with blue bristles": "TOOTHBRUSH",
    "a photo of a pink toothbrush with white and blue bristles": "TOOTHBRUSH",
    "a photo of a pink toothbrush head": "TOOTHBRUSH",
    "a photo of pink toothbrush bristles": "TOOTHBRUSH",
    "a close-up photo of a pink toothbrush": "TOOTHBRUSH",
    "a close-up photo of pink toothbrush bristles": "TOOTHBRUSH",
    "a photo of a pink toothbrush on a table": "TOOTHBRUSH",
    "a photo of a pink toothbrush on a white background": "TOOTHBRUSH",
    "a photo of a pink toothbrush on a dark background": "TOOTHBRUSH",
    "a photo of a pink toothbrush in a bathroom": "TOOTHBRUSH",
    "a photo of a used pink toothbrush": "TOOTHBRUSH",
    "a photo of a manual pink toothbrush": "TOOTHBRUSH",
    "a top-down photo of a pink toothbrush": "TOOTHBRUSH",
    "a side view photo of a pink toothbrush": "TOOTHBRUSH",
    "a horizontal pink toothbrush": "TOOTHBRUSH",
    "a vertical pink toothbrush": "TOOTHBRUSH",

    # 우유팩
    "a photo of a white milk carton": "MILK_CARTON",
    "a photo of a Seoul Milk carton": "MILK_CARTON",
    "a photo of a Korean white milk carton": "MILK_CARTON",

    # 유리
    "a photo of a glass bottle": "GLASS_BOTTLE",
    "a photo of broken glass": "BROKEN_GLASS",

    # 알 수 없는 쓰레기
    "a photo of unknown trash": "UNKNOWN",
}


# 3. 내부 타입의 한글 품목명
item_type_to_korean = {
    "PET_BOTTLE": "페트병",
    "CAN": "캔",
    "PAPER_CUP": "종이컵",
    "RECEIPT": "영수증",
    "TOOTHBRUSH": "칫솔",
    "MILK_CARTON": "서울우유 하얀 우유팩",
    "GLASS_BOTTLE": "유리병",
    "BROKEN_GLASS": "깨진 유리",
    "UNKNOWN": "알 수 없음",
}


# CLIP에 전달할 텍스트 후보 목록
candidate_labels = list(label_to_item_type.keys())


# 4. CLIP 모델 로딩
print("CLIP 모델 로딩 중입니다. 처음 실행할 때는 시간이 걸릴 수 있어요.")

model = CLIPModel.from_pretrained(MODEL_NAME)
processor = CLIPProcessor.from_pretrained(MODEL_NAME)

model.eval()

print("CLIP 모델 로딩 완료")


# 5. 웹캠 열기
camera_index = 1
cap = cv2.VideoCapture(camera_index)

if not cap.isOpened():
    print("웹캠을 열 수 없습니다.")
    print("camera_index를 1 또는 2로 바꿔보세요.")
    raise SystemExit


print("웹캠 실행 중")
print("스페이스바: 현재 화면 캡처 후 CLIP 분류")
print("q: 종료")


last_result_text = "Press SPACE to classify"


# 6. 웹캠 화면 반복
while True:
    ret, frame = cap.read()

    if not ret:
        print("프레임을 읽을 수 없습니다.")
        break

    display_frame = frame.copy()

    cv2.putText(
        display_frame,
        last_result_text,
        (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2,
    )

    cv2.imshow(
        "Sortree CLIP Webcam - Press SPACE",
        display_frame,
    )

    key = cv2.waitKey(30) & 0xFF

    # q를 누르면 종료
    if key == ord("q"):
        break

    # 스페이스바를 누르면 현재 화면 분류
    if key == ord(" "):
        print("\nCLIP 분류 중...")

        classifying_frame = frame.copy()

        cv2.putText(
            classifying_frame,
            "Classifying...",
            (20, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2,
        )

        cv2.imshow(
            "Sortree CLIP Webcam - Press SPACE",
            classifying_frame,
        )

        cv2.waitKey(1)

        # OpenCV 이미지는 BGR이므로 RGB로 변환
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb_frame)

        # CLIP 입력 데이터 생성
        inputs = processor(
            text=candidate_labels,
            images=image,
            return_tensors="pt",
            padding=True,
        )

        # 모델 추론
        with torch.no_grad():
            outputs = model(**inputs)
            logits_per_image = outputs.logits_per_image
            probs = logits_per_image.softmax(dim=1)

        # 가장 점수가 높은 후보 찾기
        best_idx = probs.argmax(dim=1).item()
        best_label = candidate_labels[best_idx]
        best_score = probs[0][best_idx].item()

        item_type = label_to_item_type[best_label]
        item_name = item_type_to_korean[item_type]

        last_result_text = f"{item_type} {best_score:.4f}"

        print("\n==============================")
        print("CLIP 분류 결과")
        print("==============================")
        print(f"가장 가까운 라벨: {best_label}")
        print(f"itemType: {item_type}")
        print(f"한글 품목명: {item_name}")
        print(f"점수: {best_score:.4f}")

        print("\n상위 후보 점수:")

        top_count = min(5, len(candidate_labels))

        top_scores, top_indices = torch.topk(
            probs[0],
            k=top_count,
        )

        for score, idx in zip(top_scores, top_indices):
            label = candidate_labels[idx.item()]
            predicted_type = label_to_item_type[label]

            print(
                f"{label} "
                f"({predicted_type}): "
                f"{score.item():.4f}"
            )

        print("==============================\n")


# 7. 웹캠 종료
cap.release()
cv2.destroyAllWindows()