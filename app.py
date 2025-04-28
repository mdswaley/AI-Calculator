from flask import Flask, render_template, Response, jsonify, request
import cv2
import pytesseract
import re

# Ensure pytesseract points to the correct path of Tesseract OCR (adjust the path as needed)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Adjust if necessary

app = Flask(__name__)

# Global variables to store detected price and quantity
price = 0.0
quantity = 1

# Function to improve text recognition by applying some pre-processing techniques
def preprocess_image(frame):
    # Convert the frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Apply some additional preprocessing to improve OCR
    # (e.g., thresholding or blurring to remove noise)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    return thresh

# Start the webcam feed
def generate_frames():
    global price
    cap = cv2.VideoCapture(0)  # Capture video from the first camera (0 for default webcam)

    while True:
        success, frame = cap.read()  # Read a frame from the webcam
        if not success:
            break
        else:
            # Preprocess the image
            processed_frame = preprocess_image(frame)

            # Use Tesseract to extract text from the processed frame
            text = pytesseract.image_to_string(processed_frame)

            # Regular expression to find the price (you can adjust this pattern as needed)
            match = re.search(r'(\d+\.\d{2})', text)  # Looks for numbers like 100.99
            if match:
                price = float(match.group(1))  # If a price is found, update the price variable

            # Display the processed frame
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

    cap.release()

# Home route
@app.route('/')
def index():
    return render_template('index.html')

# Route for video feed
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Route to get the price
@app.route('/get_price')
def get_price():
    return jsonify({'price': price})

# Route to calculate the total based on quantity
@app.route('/calculate_total', methods=['POST'])
def calculate_total():
    global price, quantity
    data = request.get_json()
    quantity = int(data.get('quantity', 1))  # Set the quantity from the frontend
    total = price * quantity
    return jsonify({'total': total})

if __name__ == '__main__':
    app.run(debug=True)
