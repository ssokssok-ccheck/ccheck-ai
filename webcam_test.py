import cv2

camera_index = 1
cap = cv2.VideoCapture(camera_index)

if not cap.isOpened():
    print("웹캠을 열 수 없습니다.")
    print("camera_index를 1 또는 2로 바꿔보세요.")
    exit()

print("웹캠 실행 중입니다.")
print("q를 누르면 종료됩니다.")

while True:
    ret, frame = cap.read()

    if not ret:
        print("프레임을 읽을 수 없습니다.")
        break

    cv2.imshow("Webcam Test", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()