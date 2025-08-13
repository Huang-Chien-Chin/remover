from flask import Flask, request, send_file, render_template, redirect, url_for
from rembg import remove
from PIL import Image
import io, os, time

app = Flask(__name__)

# 資料夾
UPLOAD_DIR = 'static/upload'
OUTPUT_DIR = 'static/output'
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 允許的副檔名（含 JFIF）
ALLOWED_EXTS = {'.png', '.jpg', '.jpeg', '.webp', '.jfif'}
def allowed_file(fn: str) -> bool:
    return os.path.splitext(fn.lower())[1] in ALLOWED_EXTS

# 首頁：只顯示上傳表單與「相簿」按鈕（不再帶相簿縮圖）
@app.route('/')
def index():
    return render_template('upload.html')

# 上傳並去背：結果檔存到 static/output，同時回傳檔案給使用者下載
@app.route('/remove-bg', methods=['POST'])
def remove_bg():
    f = request.files.get('image')
    if not f or f.filename == '':
        return ('No file uploaded', 400)

    # 開檔、去背
    img = Image.open(f.stream)
    out = remove(img)

    # 以時間戳命名並存到相簿資料夾（output）
    filename = f"no-bg-{int(time.time())}.png"
    out_path = os.path.join(OUTPUT_DIR, filename)
    out.save(out_path)

    # 下載回傳
    bio = io.BytesIO()
    out.save(bio, 'PNG')
    bio.seek(0)
    return send_file(bio, mimetype='image/png', as_attachment=True, download_name=filename)

# 相簿頁：列出所有去背完的圖片（/static/output/...）
@app.route('/gallery')
def gallery():
    files = [f for f in sorted(os.listdir(OUTPUT_DIR), reverse=True) if allowed_file(f)]
    images = [url_for('static', filename=f'output/{name}') for name in files]
    return render_template('gallery.html', images=images)

# 相簿刪除功能
@app.post('/delete/<path:filename>')
def delete_image(filename):
    # 僅允許刪除 OUTPUT_DIR 內允許副檔名的檔案
    safe_name = os.path.basename(filename)
    if not allowed_file(safe_name):
        return ('Not allowed', 400)

    target = os.path.normpath(os.path.join(OUTPUT_DIR, safe_name))
    abs_output = os.path.abspath(OUTPUT_DIR)
    if not os.path.abspath(target).startswith(abs_output):
        return ('Invalid path', 400)

    if os.path.exists(target):
        os.remove(target)
    return redirect(url_for('gallery'))

if __name__ == '__main__':
    app.run(debug=True)
