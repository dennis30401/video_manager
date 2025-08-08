
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

# 全局變量用於追蹤縮圖生成進度
thumbnail_progress = {}

# 全局變量用於追蹤正在生成縮圖的影片，防止重複生成
generating_videos = set()

def allowed_file(filename):
    return filename.lower().endswith(('.mp4', '.mkv', '.avi', '.mov'))

def is_subtitle_file(filename):
    """檢查是否為字幕檔案"""
    return filename.lower().endswith(('.srt', '.vtt', '.ass', '.ssa', '.sub', '.idx'))

def find_subtitle_files(video_path):
    """尋找與影片相關的字幕檔案"""
    video_dir = os.path.dirname(video_path)
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    
    subtitle_files = []
    
    # 搜尋相同目錄下的字幕檔案
    for file in os.listdir(video_dir):
        if is_subtitle_file(file):
            file_path = os.path.join(video_dir, file)
            file_name = os.path.splitext(file)[0]
            
            # 檢查檔案名是否匹配（相同名稱或包含影片名稱）
            if file_name == video_name or video_name in file_name:
                subtitle_info = {
                    'path': file_path,
                    'filename': file,
                    'language': detect_subtitle_language(file),
                    'format': os.path.splitext(file)[1][1:].upper(),  # 獲取副檔名
                    'size': get_readable_size(os.path.getsize(file_path))
                }
                subtitle_files.append(subtitle_info)
    
    return subtitle_files

def detect_subtitle_language(filename):
    """從檔名中檢測字幕語言"""
    filename_lower = filename.lower()
    
    # 常見語言標識
    language_map = {
        'zh': '中文',
        'cht': '繁體中文',
        'chs': '簡體中文',
        'tc': '繁體中文',
        'sc': '簡體中文',
        'cn': '簡體中文',
        'tw': '繁體中文',
        'en': '英文',
        'eng': '英文',
        'english': '英文',
        'ja': '日文',
        'jp': '日文',
        'japanese': '日文',
        'ko': '韓文',
        'kr': '韓文',
        'korean': '韓文',
        'fr': '法文',
        'french': '法文',
        'de': '德文',
        'german': '德文',
        'es': '西班牙文',
        'spanish': '西班牙文'
    }
    
    for key, value in language_map.items():
        if key in filename_lower:
            return value
    
    return '未知'

def validate_subtitle_content(subtitle_path):
    """驗證字幕檔案內容是否有效"""
    try:
        with open(subtitle_path, 'r', encoding='utf-8') as f:
            content = f.read(1000)  # 讀取前1000字符
            
        # 基本驗證邏輯
        if subtitle_path.endswith('.srt'):
            # SRT格式應該包含時間戳記
            return '-->' in content and any(char.isdigit() for char in content)
        elif subtitle_path.endswith('.vtt'):
            # VTT格式應該以WEBVTT開頭
            return content.startswith('WEBVTT')
        else:
            # 其他格式基本檢查
            return len(content.strip()) > 0
            
    except Exception:
        return False

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

def generate_multi_thumbnails(video_path, timestamps=None, progress_callback=None):
    """生成多個時間點的縮圖"""
    directory = os.path.dirname(video_path)
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    
    # 如果沒有指定時間點，使用預設的 10%, 30%, 50%, 70%, 90%
    if timestamps is None:
        # 先獲取影片總時長
        try:
            # 使用當前目錄的FFprobe
            ffprobe_path = os.path.join(os.path.dirname(__file__), 'ffprobe.exe')
            if not os.path.exists(ffprobe_path):
                ffprobe_path = 'ffprobe'  # 回退到系統PATH中的ffprobe
            
            result = subprocess.run(
                [ffprobe_path, '-v', 'error', '-show_entries',
                 'format=duration', '-of',
                 'default=noprint_wrappers=1:nokey=1', video_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
            duration = float(result.stdout)
            # 生成 5 個時間點的縮圖
            timestamps = [
                duration * 0.1,   # 10%
                duration * 0.3,   # 30% 
                duration * 0.5,   # 50%
                duration * 0.7,   # 70%
                duration * 0.9    # 90%
            ]
        except Exception as e:
            print(f"獲取影片時長失敗: {e}")
            # 如果獲取時長失敗，使用固定秒數
            timestamps = [10, 30, 60, 90, 120]
    
    thumbnails = []
    total_timestamps = len(timestamps)
    
    if progress_callback:
        progress_callback(0, total_timestamps, f"開始生成 {total_timestamps} 個縮圖...")
    
    for i, timestamp in enumerate(timestamps):
        thumbnail_path = os.path.join(directory, f"{base_name}_thumb_{i+1}.png")
        
        if progress_callback:
            progress_callback(i, total_timestamps, f"正在處理第 {i+1} 個縮圖...")
        
        # 如果縮圖已存在，跳過生成
        if os.path.exists(thumbnail_path):
            thumbnails.append({
                'path': thumbnail_path,
                'timestamp': timestamp,
                'index': i + 1
            })
            if progress_callback:
                progress_callback(i+1, total_timestamps, f"第 {i+1} 個縮圖已存在，跳過生成")
            continue
        
        # 將秒數轉換為 HH:MM:SS 格式
        hours = int(timestamp // 3600)
        minutes = int((timestamp % 3600) // 60)
        seconds = int(timestamp % 60)
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        # 使用當前目錄的FFmpeg
        ffmpeg_path = os.path.join(os.path.dirname(__file__), 'ffmpeg.exe')
        if not os.path.exists(ffmpeg_path):
            ffmpeg_path = 'ffmpeg'  # 回退到系統PATH中的ffmpeg
        
        command = [
            ffmpeg_path,
            '-y',                 # 自動覆蓋舊檔
            '-i', video_path,
            '-ss', time_str,
            '-vframes', '1',
            '-vf', 'scale=320:180',  # 縮圖尺寸
            thumbnail_path
        ]
        
        try:
            result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if os.path.exists(thumbnail_path):
                thumbnails.append({
                    'path': thumbnail_path,
                    'timestamp': timestamp,
                    'index': i + 1
                })
                if progress_callback:
                    progress_callback(i+1, total_timestamps, f"成功生成第 {i+1} 個縮圖")
                print(f"成功生成縮圖: {thumbnail_path}")
        except subprocess.CalledProcessError as e:
            print(f"生成縮圖失敗 {thumbnail_path}: {e}")
            if progress_callback:
                progress_callback(i+1, total_timestamps, f"第 {i+1} 個縮圖生成失敗")
            continue
    
    if progress_callback:
        progress_callback(total_timestamps, total_timestamps, f"完成！成功生成 {len(thumbnails)} 個縮圖")
    
    return thumbnails

def get_video_info(video_path):
    """獲取影片詳細資訊"""
    try:
        # 獲取影片時長
        duration_result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries',
             'format=duration', '-of',
             'default=noprint_wrappers=1:nokey=1', video_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        duration_seconds = float(duration_result.stdout)
        
        # 獲取影片解析度
        resolution_result = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
             '-show_entries', 'stream=width,height', '-of',
             'default=noprint_wrappers=1:nokey=1', video_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        resolution_lines = resolution_result.stdout.decode().strip().split('\n')
        width = int(resolution_lines[0]) if len(resolution_lines) > 0 else 0
        height = int(resolution_lines[1]) if len(resolution_lines) > 1 else 0
        
        return {
            'duration_seconds': duration_seconds,
            'width': width,
            'height': height,
            'resolution': f"{width}x{height}"
        }
    except Exception as e:
        print(f"獲取影片資訊失敗 {video_path}: {e}")
        return {
            'duration_seconds': 0,
            'width': 0,
            'height': 0,
            'resolution': "未知"
        }

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

@app.route('/api/tags', methods=['GET'])
def get_all_tags():
    """獲取所有已存在的標籤，用於自動完成"""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            videos = json.load(f)
        
        all_tags = set()
        for video in videos:
            if 'tag' in video and isinstance(video['tag'], list):
                all_tags.update(video['tag'])
        
        # 按字母順序排序
        sorted_tags = sorted(list(all_tags))
        return jsonify(sorted_tags)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tags/stats', methods=['GET'])
def get_tag_stats():
    """獲取標籤統計信息"""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            videos = json.load(f)
        
        tag_counts = {}
        for video in videos:
            if 'tag' in video and isinstance(video['tag'], list):
                for tag in video['tag']:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # 按使用頻率排序
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        return jsonify(sorted_tags)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/videos/<int:index>', methods=['PUT'])
def update_video(index):
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            videos = json.load(f)
        
        if index >= len(videos):
            return jsonify({"error": "影片索引不存在"}), 404
            
        data = request.json
        for key in ['filename', 'tag', 'description']:
            if key == 'tag':
                if isinstance(data[key], str):
                    # 處理逗號分隔的字符串
                    videos[index][key] = [tag.strip() for tag in data[key].split(',') if tag.strip()]
                elif isinstance(data[key], list):
                    # 處理陣列，移除空白和重複
                    videos[index][key] = list(set([str(tag).strip() for tag in data[key] if str(tag).strip()]))
                else:
                    videos[index][key] = []
            else:
                videos[index][key] = data[key]
        
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(videos, f, indent=4, ensure_ascii=False)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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

@app.route('/api/videos/<int:index>/multi_thumbnails', methods=['GET'])
def get_multi_thumbnails(index):
    """獲取指定影片的多時間點縮圖"""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            videos = json.load(f)
        
        if index >= len(videos):
            return jsonify({"error": "影片索引不存在"}), 404
        
        video = videos[index]
        video_path = video['path']
        
        if not os.path.exists(video_path):
            return jsonify({"error": "影片檔案不存在"}), 404
        
        # 檢查是否已有多時間點縮圖資料
        if 'multi_thumbnails' in video and video['multi_thumbnails']:
            # 驗證縮圖檔案是否存在
            valid_thumbnails = []
            for thumb in video['multi_thumbnails']:
                if os.path.exists(thumb['path']):
                    valid_thumbnails.append(thumb)
            
            if valid_thumbnails:
                return jsonify(valid_thumbnails)
        
        # 如果沒有縮圖，返回空數組，讓前端決定是否要生成
        return jsonify([])
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/videos/<int:index>/generate_thumbnails', methods=['POST'])
def generate_thumbnails_for_video(index):
    """為指定影片生成多時間點縮圖"""
    try:
        # 檢查是否已經在生成縮圖
        video_key = f"video_{index}"
        if video_key in generating_videos:
            print(f"影片 {index} 正在生成縮圖中，跳過重複請求")
            return jsonify({"error": "該影片正在生成縮圖中，請稍候"}), 409
        
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            videos = json.load(f)
        
        if index >= len(videos):
            return jsonify({"error": "影片索引不存在"}), 404
        
        video = videos[index]
        video_path = video['path']
        
        if not os.path.exists(video_path):
            return jsonify({"error": "影片檔案不存在"}), 404
        
        # 標記為正在生成
        generating_videos.add(video_key)
        print(f"開始為影片 {index} 生成縮圖，當前生成隊列: {generating_videos}")
        
        # 獲取自定義時間點（如果有提供）
        data = request.get_json() or {}
        custom_timestamps = data.get('timestamps')
        
        # 生成多時間點縮圖，並提供進度回調
        def progress_callback(completed, total, message):
            # 保存進度到全局變量
            progress_key = f"video_{index}"
            thumbnail_progress[progress_key] = {
                'completed': completed,
                'total': total,
                'message': message,
                'percentage': int((completed / total) * 100) if total > 0 else 0
            }
            print(f"縮圖生成進度 [{progress_key}]: {completed}/{total} ({int((completed / total) * 100) if total > 0 else 0}%) - {message}")
        
        # 初始化進度
        progress_key = f"video_{index}"
        initial_total = len(custom_timestamps) if custom_timestamps else 5
        thumbnail_progress[progress_key] = {
            'completed': 0,
            'total': initial_total,
            'message': f'準備開始生成 {initial_total} 個縮圖...',
            'percentage': 0
        }
        print(f"初始化進度追蹤 [{progress_key}]: 準備生成 {initial_total} 個縮圖")
        
        thumbnails = generate_multi_thumbnails(video_path, custom_timestamps, progress_callback)
        
        # 清除進度記錄和生成標記
        if progress_key in thumbnail_progress:
            del thumbnail_progress[progress_key]
        generating_videos.discard(video_key)
        print(f"影片 {index} 縮圖生成完成，移除生成標記，當前生成隊列: {generating_videos}")
        
        # 更新影片資料
        video['multi_thumbnails'] = thumbnails
        
        # 獲取並更新影片資訊
        video_info = get_video_info(video_path)
        video.update(video_info)
        
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(videos, f, indent=4, ensure_ascii=False)
        
        return jsonify({
            'status': 'success',
            'thumbnails': thumbnails,
            'completed': len(thumbnails),
            'total': len(custom_timestamps) if custom_timestamps else 5,
            'message': f'成功生成 {len(thumbnails)} 個縮圖'
        })
    
    except Exception as e:
        # 出現異常時也要清除標記
        video_key = f"video_{index}"
        generating_videos.discard(video_key)
        progress_key = f"video_{index}"
        if progress_key in thumbnail_progress:
            del thumbnail_progress[progress_key]
        print(f"影片 {index} 縮圖生成失敗，清除標記: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/videos/<int:index>/thumbnail_progress', methods=['GET'])
def get_thumbnail_progress(index):
    """獲取縮圖生成進度"""
    progress_key = f"video_{index}"
    
    if progress_key in thumbnail_progress:
        return jsonify(thumbnail_progress[progress_key])
    else:
        return jsonify({
            'completed': 0,
            'total': 0,
            'message': '無進行中的縮圖生成',
            'percentage': 0
        })

@app.route('/api/multi_thumbnail')
def get_multi_thumbnail():
    """提供多時間點縮圖服務"""
    path = urllib.parse.unquote(request.args.get('path'))
    if not path or not os.path.exists(path):
        return "Thumbnail not found", 404
    return send_file(path, mimetype='image/png')

@app.route('/api/videos/<int:index>/video_info', methods=['GET'])
def get_video_detailed_info(index):
    """獲取影片詳細資訊"""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            videos = json.load(f)
        
        if index >= len(videos):
            return jsonify({"error": "影片索引不存在"}), 404
        
        video = videos[index]
        video_path = video['path']
        
        if not os.path.exists(video_path):
            return jsonify({"error": "影片檔案不存在"}), 404
        
        # 獲取詳細資訊
        video_info = get_video_info(video_path)
        
        # 合併現有資料
        result = {**video, **video_info}
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/videos/<int:index>/subtitles', methods=['GET'])
def get_video_subtitles(index):
    """獲取指定影片的字幕檔案"""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            videos = json.load(f)
        
        if index >= len(videos):
            return jsonify({"error": "影片索引不存在"}), 404
        
        video = videos[index]
        video_path = video['path']
        
        if not os.path.exists(video_path):
            return jsonify({"error": "影片檔案不存在"}), 404
        
        # 搜尋字幕檔案
        subtitle_files = find_subtitle_files(video_path)
        
        # 驗證字幕檔案
        valid_subtitles = []
        for subtitle in subtitle_files:
            if validate_subtitle_content(subtitle['path']):
                valid_subtitles.append(subtitle)
        
        # 更新影片資料中的字幕資訊
        video['subtitles'] = valid_subtitles
        
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(videos, f, indent=4, ensure_ascii=False)
        
        return jsonify(valid_subtitles)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/subtitle')
def serve_subtitle():
    """提供字幕檔案服務"""
    subtitle_path = urllib.parse.unquote(request.args.get('path'))
    if not subtitle_path or not os.path.exists(subtitle_path):
        return "Subtitle not found", 404
    
    # 根據字幕格式設定MIME類型
    if subtitle_path.endswith('.vtt'):
        mimetype = 'text/vtt'
    elif subtitle_path.endswith('.srt'):
        mimetype = 'text/plain'
    else:
        mimetype = 'text/plain'
    
    return send_file(subtitle_path, mimetype=mimetype)

@app.route('/api/videos/<int:index>/upload_subtitle', methods=['POST'])
def upload_subtitle(index):
    """上傳字幕檔案"""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            videos = json.load(f)
        
        if index >= len(videos):
            return jsonify({'error': '影片索引不存在'}), 404
        
        if 'file' not in request.files:
            return jsonify({'error': '沒有檔案'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '檔名為空'}), 400
        
        if not is_subtitle_file(file.filename):
            return jsonify({'error': '僅支援字幕檔案格式 (.srt, .vtt, .ass, .ssa, .sub, .idx)'}), 400
        
        video = videos[index]
        video_path = video['path']
        video_dir = os.path.dirname(video_path)
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        
        # 生成字幕檔案名稱
        file_ext = os.path.splitext(file.filename)[1]
        language = request.form.get('language', '')
        if language:
            subtitle_filename = f"{video_name}.{language}{file_ext}"
        else:
            subtitle_filename = f"{video_name}{file_ext}"
        
        subtitle_path = os.path.join(video_dir, subtitle_filename)
        
        # 儲存檔案
        file.save(subtitle_path)
        
        # 驗證檔案內容
        if not validate_subtitle_content(subtitle_path):
            os.remove(subtitle_path)  # 刪除無效檔案
            return jsonify({'error': '字幕檔案格式無效'}), 400
        
        # 重新掃描字幕檔案
        subtitle_files = find_subtitle_files(video_path)
        video['subtitles'] = subtitle_files
        
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(videos, f, indent=4, ensure_ascii=False)
        
        return jsonify({
            'status': '字幕上傳成功',
            'subtitle_path': subtitle_path,
            'subtitles': subtitle_files
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/videos/<int:index>/delete_subtitle', methods=['DELETE'])
def delete_subtitle(index):
    """刪除字幕檔案"""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            videos = json.load(f)
        
        if index >= len(videos):
            return jsonify({'error': '影片索引不存在'}), 404
        
        data = request.get_json()
        subtitle_path = data.get('subtitle_path')
        
        if not subtitle_path or not os.path.exists(subtitle_path):
            return jsonify({'error': '字幕檔案不存在'}), 404
        
        # 刪除檔案
        os.remove(subtitle_path)
        
        # 更新影片資料
        video = videos[index]
        video_path = video['path']
        subtitle_files = find_subtitle_files(video_path)
        video['subtitles'] = subtitle_files
        
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(videos, f, indent=4, ensure_ascii=False)
        
        return jsonify({
            'status': '字幕刪除成功',
            'subtitles': subtitle_files
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/convert_subtitle', methods=['POST'])
def convert_subtitle_format():
    """轉換字幕格式（SRT <-> VTT）"""
    try:
        data = request.get_json()
        source_path = data.get('source_path')
        target_format = data.get('target_format', 'vtt')  # 'srt' 或 'vtt'
        
        if not source_path or not os.path.exists(source_path):
            return jsonify({'error': '來源字幕檔案不存在'}), 404
        
        # 讀取來源檔案
        with open(source_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 生成目標檔案路徑
        source_dir = os.path.dirname(source_path)
        source_name = os.path.splitext(os.path.basename(source_path))[0]
        target_path = os.path.join(source_dir, f"{source_name}.{target_format}")
        
        # 轉換邏輯（簡單實現）
        if target_format == 'vtt' and source_path.endswith('.srt'):
            # SRT to VTT
            converted_content = srt_to_vtt(content)
        elif target_format == 'srt' and source_path.endswith('.vtt'):
            # VTT to SRT
            converted_content = vtt_to_srt(content)
        else:
            return jsonify({'error': '不支援的轉換格式'}), 400
        
        # 儲存轉換後的檔案
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(converted_content)
        
        return jsonify({
            'status': '轉換成功',
            'target_path': target_path
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def srt_to_vtt(srt_content):
    """將SRT格式轉換為VTT格式"""
    lines = srt_content.strip().split('\n')
    vtt_lines = ['WEBVTT\n']
    
    for line in lines:
        if '-->' in line:
            # 轉換時間格式
            line = line.replace(',', '.')
        vtt_lines.append(line)
    
    return '\n'.join(vtt_lines)

def vtt_to_srt(vtt_content):
    """將VTT格式轉換為SRT格式"""
    lines = vtt_content.strip().split('\n')
    srt_lines = []
    subtitle_index = 1
    
    for line in lines:
        if line.startswith('WEBVTT'):
            continue
        elif '-->' in line:
            # 添加字幕索引
            srt_lines.append(str(subtitle_index))
            subtitle_index += 1
            # 轉換時間格式
            line = line.replace('.', ',')
        
        srt_lines.append(line)
    
    return '\n'.join(srt_lines)

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
