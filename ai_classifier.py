# ai_classifier.py

import cv2
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from config import ITEM_NAME_KO


MODEL_NAME = "openai/clip-vit-base-patch32"

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

    "a photo of a toothbrush": "TOOTHBRUSH",
    "a photo of a used toothbrush": "TOOTHBRUSH",
    "a photo of a plastic toothbrush": "TOOTHBRUSH",
    "a photo of a toothbrush with blue bristles": "TOOTHBRUSH",
    "a photo of a toothbrush with a white handle and blue bristles": "TOOTHBRUSH",
    "a photo of a white toothbrush with blue bristles": "TOOTHBRUSH",
    "a photo of a blue and white toothbrush": "TOOTHBRUSH",

    "a photo of a white milk carton": "MILK_CARTON",
    "a photo of a Seoul Milk carton": "MILK_CARTON",
    "a photo of a Korean white milk carton": "MILK_CARTON",

    "a photo of a glass bottle": "GLASS_BOTTLE",
    "a photo of broken glass": "BROKEN_GLASS",
    "a photo of unknown trash": "UNKNOWN"
}

candidate_labels = list(label_to_item_type.keys())

device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"CLIP 사용 장치: {device}")

model = CLIPModel.from_pretrained(MODEL_NAME).to(device)
processor = CLIPProcessor.from_pretrained(MODEL_NAME)
model.eval()


def classify_frame(frame):
    """
    웹캠 frame을 받아서 CLIP으로 품목을 분류한다.
    """

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(rgb_frame)

    inputs = processor(
        text=candidate_labels,
        images=image,
        return_tensors="pt",
        padding=True
    )

    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        probs = outputs.logits_per_image.softmax(dim=1)

    best_idx = probs.argmax().item()
    best_label = candidate_labels[best_idx]
    best_score = probs[0][best_idx].item()

    item_type = label_to_item_type[best_label]
    item_name = ITEM_NAME_KO[item_type]

    return {
        "itemType": item_type,
        "itemName": item_name,
        "aiLabel": best_label,
        "aiScore": round(best_score, 4)
    }