import os
import uuid
import cv2
import numpy as np
import easyocr
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, render_template, request, send_file

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 初始化 EasyOCR 识别器
reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['image']
        if file:
            img_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(img_path)

            # OCR 识别
            results = reader.readtext(img_path)
            boxes = []
            for i, (bbox, text, conf) in enumerate(results):
                box = {
                    'index': i,
                    'text': text,
                    'coords': bbox
                }
                boxes.append(box)

            return render_template('index.html', image=file.filename, boxes=boxes)

    return render_template('index.html')

@app.route('/modify', methods=['POST'])
def modify():
    text = request.form.get('new_text')
    index = int(request.form.get('index'))
    filename = request.form.get('filename')

    path = os.path.join(UPLOAD_FOLDER, filename)
    image = cv2.imread(path)
    reader_result = reader.readtext(path)

    # 获取目标文字框坐标
    target_box = reader_result[index][0]
    x1, y1 = map(int, target_box[0])
    x2, y2 = map(int, target_box[2])

    # 创建掩膜（mask）用于 inpainting
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)

    # 自动背景修复
    inpainted = cv2.inpaint(image, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)

    # 转换为 PIL 图像以写入新文字
    pil_img = Image.fromarray(inpainted)
    draw = ImageDraw.Draw(pil_img)

    # 动态字体大小（高度的 85%）
    font_size = max(10, int((y2 - y1) * 0.85))
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()

    draw.text((x1, y1), text, fill='black', font=font)

    # 保存新图像
    new_filename = f"modified_{uuid.uuid4().hex[:8]}.png"
    new_path = os.path.join(UPLOAD_FOLDER, new_filename)
    pil_img.save(new_path)

    return send_file(new_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
