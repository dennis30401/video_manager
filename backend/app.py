
import os
import json
import urllib.parse
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import mimetypes
import subprocess
import datetime

app = Flask(__name__)
CORS(app)

DATA_FILE = 'data.json'
LAST_PATH_FILE = 'last_path.json'

def allowed_file(filename):
    return filename.lower().endswith(('.mp4', '.mkv', '.avi', '.mov'))

def get_video_duration(path):
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries',
             'format=duration', '-of',
             'default=noprint_wrappers=1:nokey=1', path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        duration = float(result.stdout)
        mins = int(duration // 60)
        secs = int(duration % 60)
        return f"{mins}:{secs:02d}"
    except:
        return "未知"

def generate_thumbnail(video_path):
    directory = os.path.dirname(video_path)
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    thumbnail_path = os.path.join(directory, base_name + '.png')

    if os.path.exists(thumbnail_path):
        return thumbnail_path  # 已有縮圖就直接用

    command = [
        'ffmpeg',
        '-y',                 # 自動覆蓋舊檔（如果有的話）
        '-i', video_path,
        '-ss', '00:00:50',
        '-vframes', '1',
        thumbnail_path
    ]

    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if os.path.exists(thumbnail_path):
            return thumbnail_path
    except subprocess.CalledProcessError:
        pass

    return ""  # 如果產生失敗，回傳空字串

def get_readable_size(size_bytes):
    for unit in ['Bytes', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"

@app.route('/api/videos', methods=['GET'])
def get_videos():
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        videos = json.load(f)
    return jsonify(videos)

@app.route('/api/videos/<int:index>', methods=['PUT'])
def update_video(index):
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        videos = json.load(f)
    data = request.json
    for key in ['filename', 'tag', 'description']:
        if key == 'tag' and isinstance(data[key], str):
            videos[index][key] = [tag.strip() for tag in data[key].split(',') if tag.strip()]
        else:
            videos[index][key] = data[key]
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(videos, f, indent=4, ensure_ascii=False)
    return jsonify({"status": "success"})

@app.route('/api/scan', methods=['POST'])
def scan_videos():
    scan_path = urllib.parse.unquote(request.json.get('path'))
    if not scan_path or not os.path.exists(scan_path):
        return jsonify({"error": "請提供有效的資料夾路徑"}), 400
    print(scan_path)
    # 正確做法：讀
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        videos = json.load(f)

    # 移除不存在檔案
    videos = [v for v in videos if os.path.exists(v['path'])]

    existing_files = set(v['path'] for v in videos)
    new_files = []

    for root, dirs, files in os.walk(scan_path):
        for file in files:
            if allowed_file(file):
                full_path = os.path.join(root, file)
                print(full_path)
                if full_path not in existing_files:
                    name, _ = os.path.splitext(file)
                    thumb = generate_thumbnail(full_path)
                    current_time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                    videos.append({
                        "filename": file,
                        "tag": [],
                        "path": full_path,
                        "description": "",
                        "duration": get_video_duration(full_path),
                        "thumbnail": thumb,
                        "size": get_readable_size(os.path.getsize(full_path)),
                        "add_time": current_time  # 添加掃描時間  
                    })
                    new_files.append(full_path)

    # 正確做法：寫
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(videos, f, indent=4, ensure_ascii=False)

    return jsonify({"added": new_files, "total": len(videos)})

@app.route('/api/last_path', methods=['GET', 'POST'])
def last_path():
    if request.method == 'POST':
        path = request.json.get('path')
        with open(LAST_PATH_FILE, 'w', encoding='utf-8') as f:
            json.dump({"path": path}, f)
        return jsonify({"status": "saved"})
    else:
        if os.path.exists(LAST_PATH_FILE):
            with open(LAST_PATH_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify(data)
        return jsonify({"path": ""})

@app.route('/api/stream_video')
def stream_video():
    path = urllib.parse.unquote(request.args.get('path'))
    if not path or not os.path.exists(path):
        return "File not found", 404
    mime = mimetypes.guess_type(path)[0] or 'video/mp4'
    return send_file(path, mimetype=mime)

@app.route('/api/thumbnail')
def get_thumbnail():
    path = urllib.parse.unquote(request.args.get('path'))
    if not path or not os.path.exists(path):
        return send_file('static/thumbnails/default.png', mimetype='image/png')
    return send_file(path, mimetype='image/png')

@app.route('/api/upload_thumbnail/<int:index>', methods=['POST'])
def upload_thumbnail(index):
    if 'file' not in request.files:
        return jsonify({'error': '沒有檔案'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '檔名為空'}), 400
    if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        return jsonify({'error': '僅支援 jpg/jpeg/png'}), 400

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        videos = json.load(f)

    video = videos[index]
    video_path = video['path']
    directory = os.path.dirname(video_path)
    new_thumb = os.path.join(directory, os.path.splitext(os.path.basename(video_path))[0] + '.jpg')
    file.save(new_thumb)
    video['thumbnail'] = new_thumb

    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(videos, f, indent=4, ensure_ascii=False)

    return jsonify({'status': '縮圖已更新'})

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/api/videos/<int:index>', methods=['DELETE'])
def delete_video(index):
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        videos = json.load(f)
    
    path = videos[index]['path']
    print(path)
    new_videos = [v for v in videos if v['path'] != path]
    print(new_videos)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_videos, f, indent=4, ensure_ascii=False)
    return jsonify({'status': 'deleted'})

@app.route('/api/videos/delete_batch', methods=['POST'])
def delete_batch():
    data = request.get_json()
    indexes = data.get('indexes', [])

    # 讀取目前影片清單
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        videos = json.load(f)

    # 按 index 排除要刪掉的影片
    new_videos = [v for i, v in enumerate(videos) if i not in indexes]

    # 存回檔案
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_videos, f, indent=4, ensure_ascii=False)

    return jsonify({'status': 'deleted'})

@app.route('/api/videos/reorder', methods=['POST'])
def reorder_videos():
    videos = request.get_json()
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(videos, f, indent=4, ensure_ascii=False)
    return jsonify({'status': '排序已更新'})
