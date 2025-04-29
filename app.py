from flask import Flask, render_template, Response, jsonify, request
import cv2
import pytesseract
import re

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

app = Flask(__name__)

# Global variables
price = 0.0
quantity = 1

def preprocess_image(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    return thresh

def generate_frames():
    global price
    cap = cv2.VideoCapture(0)
    custom_config = r'--oem 3 --psm 11'

    while True:
        success, frame = cap.read()
        if not success:
            break

        processed_frame = preprocess_image(frame)

        # OCR processing
        text = pytesseract.image_to_string(processed_frame, config=custom_config)
        print("OCR Text:", text)

        # Search for price with prefix Rs, ₹, or MRP (case-insensitive)
        match = re.search(r'(?:Rs\.?|₹|MRP\.?)\s*[:\-]?\s*([\d,]*\d+\.\d{2})', text, re.IGNORECASE)
        print("Match found:", match.group(0) if match else "No match")
        if match:
            price_str = match.group(1).replace(',', '')
            try:
                price = float(price_str)
                print("Detected Price:", price)
            except ValueError:
                print("Invalid price format:", price_str)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

    cap.release()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_price')
def get_price():
    global price
    return jsonify({'price': price})

@app.route('/calculate_total', methods=['POST'])
def calculate_total():
    global price
    data = request.get_json()
    quantity = int(data.get('quantity', 1))
    total = price * quantity
    return jsonify({'total': total})

if __name__ == '__main__':
    app.run(debug=True)