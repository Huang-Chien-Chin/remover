from flask import Flask, request, render_template, jsonify, url_for, redirect
from rembg import remove
from PIL import Image
import io, os, time

app = Flask(__name__)

# 目錄
UPLOAD_DIR = 'static/upload'
OUTPUT_DIR = 'static/output'
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 支援的副檔名
ALLOWED_EXTS = {'.png', '.jpg', '.jpeg', '.webp', '.jfif', '.bmp'}
def allowed_file(fn: str) -> bool:
    return os.path.splitext(fn.lower())[1] in ALLOWED_EXTS

@app.route('/')
def index():
    return render_template('upload.html')

# 去背：存檔到 static/output，回傳 JSON（不再 as_attachment）
@app.route('/remove-bg', methods=['POST'])
def remove_bg():
    f = request.files.get('image')
    if not f or f.filename == '':
        return ('No file uploaded', 400)

    img = Image.open(f.stream)
    out = remove(img)

    filename = f"no-bg-{int(time.time())}.png"
    out_path = os.path.join(OUTPUT_DIR, filename)
    out.save(out_path)

    # 回 JSON，讓前端自己抓檔案並觸發下載
    return jsonify({
        "filename": filename,
        "url": url_for('static', filename=f'output/{filename}', _external=False)
    })

# 相簿頁
@app.route('/gallery')
def gallery():
    files = [f for f in sorted(os.listdir(OUTPUT_DIR), reverse=True) if allowed_file(f)]
    images = [url_for('static', filename=f'output/{name}') for name in files]
    return render_template('gallery.html', images=images)

# 刪除圖片（於相簿頁使用）
@app.post('/delete/<path:filename>')
def delete_image(filename):
    safe_name = os.path.basename(filename)
    if not allowed_file(safe_name):
        return ('Not allowed', 400)
    target = os.path.normpath(os.path.join(OUTPUT_DIR, safe_name))
    abs_output = os.path.abspath(OUTPUT_DIR)
    if not os.path.abspath(target).startswith(abs_output):
        return ('Invalid path', 400)
    if os.path.exists(target):
        os.remove(target)
    return redirect('/gallery')

if __name__ == '__main__':
    app.run(debug=True)
