import cv2

cap = cv2.VideoCapture(0)
if cap.isOpened():
    print("✓ Camera is accessible")
    ret, frame = cap.read()
    if ret:
        print("✓ Camera is working!")
        cv2.imshow('Camera Test', frame)
        cv2.waitKey(3000)  # Show for 3 seconds
    else:
        print("✗ Can't read from camera")
else:
    print("✗ Can't open camera")
cap.release()
cv2.destroyAllWindows()