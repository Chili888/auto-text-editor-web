import os
from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont
import easyocr
import numpy as np
import cv2
import uuid

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ✅ 禁用 GPU
reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['image']
        img_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(img_path)

        results = reader.readtext(img_path)
        boxes = []
        for i, (bbox, text, _) in enumerate(results):
            boxes.append({
                'index': i,
                'text': text,
                'coords': bbox
            })

        return render_template('index.html', image=file.filename, boxes=boxes)
    return render_template('index.html')

@app.route('/modify', methods=['POST'])
def modify():
    new_text = request.form['new_text']
    index = int(request.form['index'])
    filename = request.form['filename']

    path = os.path.join(UPLOAD_FOLDER, filename)
    image = cv2.imread(path)
    results = reader.readtext(path)
    bbox = results[index][0]

    x1, y1 = map(int, bbox[0])
    x2, y2 = map(int, bbox[2])
    cv2.rectangle(image, (x1, y1), (x2, y2), (255, 255, 255), -1)

    pil_img = Image.fromarray(image)
    draw = ImageDraw.Draw(pil_img)
    font = ImageFont.truetype("arial.ttf", 20)  # 或指定更轻量字体
    draw.text((x1, y1), new_text, fill='black', font=font)

    new_filename = f'modified_{uuid.uuid4().hex[:8]}.png'
    output_path = os.path.join(UPLOAD_FOLDER, new_filename)
    pil_img.save(output_path)

    return send_file(output_path, as_attachment=True)
