import cv2

print("Searching for cameras...")
working_cameras = []

for i in range(5):  # Check indices 0-4
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"✓ Camera found at index {i}")
            working_cameras.append(i)
        cap.release()
    else:
        print(f"✗ No camera at index {i}")

if working_cameras:
    print(f"\nWorking cameras: {working_cameras}")
    print(f"Use index {working_cameras[0]} in your code")
else:
    print("\n⚠ No cameras detected!")
    print("Possible issues:")
    print("1. Camera drivers not installed")
    print("2. Camera disabled in Device Manager")
    print("3. Camera being used by another app")