# 🎬 Video Manager - 本地影片管理系統

一個功能完整的本地影片管理系統，基於 Vue.js 3 和 Flask 開發，提供智慧影片分類、多時間點縮圖預覽、字幕管理等先進功能。

## ✨ 功能特色

### 🎯 核心功能
- **智慧影片掃描**：自動掃描指定資料夾，提取影片資訊
- **縮圖自動生成**：支援單一縮圖和多時間點縮圖（10%, 30%, 50%, 70%, 90%）
- **標籤管理系統**：支援標籤自動完成、統計分析、批量編輯
- **字幕檔案管理**：自動識別、格式轉換（SRT/VTT）、語言檢測
- **批量操作**：支援多選、批量刪除、批量標籤編輯

### 🎮 播放體驗
- **播放列表功能**：建立自訂播放清單
- **播放位置記憶**：自動記錄上次播放位置
- **自動播放**：支援自動播放下一部影片
- **隨機播放模式**：隨機播放列表功能
- **播放統計記錄**：追蹤播放次數和時長

### 🎨 進階功能
- **拖拽排序**：影片列表支援拖拽重新排序
- **響應式設計**：適配桌面和行動裝置
- **即時進度顯示**：縮圖生成進度即時追蹤
- **檔案資訊展示**：影片解析度、檔案大小、時長等
- **搜尋和篩選**：快速找到想要的影片

## 🏗️ 技術架構

### 後端技術棧
- **Python Flask**：輕量級 Web 框架
- **FFmpeg**：影片處理和縮圖生成
- **JSON 資料庫**：輕量級資料存儲
- **CORS 支援**：跨域請求處理

### 前端技術棧
- **Vue.js 3**：使用 Composition API
- **Vite**：高效能建置工具
- **Axios**：HTTP 請求處理
- **CSS3**：現代樣式設計

### 專案結構
```
video_manager/
├── backend/
│   ├── app.py                 # Flask 主應用程式
│   ├── requirements.txt       # Python 依賴清單
│   ├── data.json             # 影片資料存儲
│   └── last_path.json        # 上次掃描路徑記錄
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── List.vue      # 影片列表主組件
│   │   │   ├── MultiThumbnailViewer.vue  # 多時間點縮圖檢視器
│   │   │   └── SubtitleManager.vue       # 字幕管理組件
│   │   ├── main.js           # 前端入口
│   │   └── style.css         # 全域樣式
│   ├── package.json          # Node.js 依賴清單
│   └── vite.config.js        # Vite 配置
├── start_backend.bat         # 後端啟動腳本
├── start_frontend.bat        # 前端啟動腳本
├── start_video_manager.bat   # 一鍵啟動腳本
└── README.md                 # 專案說明文件
```

## 🚀 快速開始

### 系統需求
- **Python 3.8+**
- **Node.js 16+**
- **FFmpeg**（用於影片處理）

### 一鍵啟動（推薦）
```bash
# 雙擊執行一鍵啟動腳本
start_video_manager.bat
```

### 手動安裝

#### 1. 後端設置
```bash
cd backend
python -m venv venv
call venv\Scripts\activate  # Windows
pip install -r requirements.txt
python app.py
```

#### 2. 前端設置
```bash
cd frontend
npm install
npm run dev
```

#### 3. 訪問應用
- **前端介面**：http://localhost:5173
- **後端 API**：http://127.0.0.1:5000

## 📚 使用指南

### 基本操作
1. **掃描影片**：點擊「掃描資料夾」選擇影片目錄
2. **播放影片**：點擊影片標題開始播放
3. **編輯資訊**：點擊「編輯」修改影片描述和標籤
4. **查看縮圖**：點擊「縮圖」查看多時間點預覽

### 進階功能
- **批量操作**：勾選多個影片後使用批量功能
- **標籤管理**：使用逗號分隔多個標籤
- **字幕管理**：自動識別同目錄下的字幕檔案
- **播放列表**：建立並管理自訂播放清單

## 🔧 API 文件

### 影片管理
- `GET /api/videos` - 獲取所有影片
- `PUT /api/videos/{index}` - 更新影片資訊
- `DELETE /api/videos/{index}` - 刪除影片
- `POST /api/videos/delete_batch` - 批量刪除
- `POST /api/videos/reorder` - 重新排序

### 縮圖功能
- `GET /api/videos/{index}/multi_thumbnails` - 獲取多時間點縮圖
- `POST /api/videos/{index}/generate_thumbnails` - 生成縮圖
- `GET /api/videos/{index}/thumbnail_progress` - 獲取生成進度

### 字幕管理
- `GET /api/videos/{index}/subtitles` - 獲取字幕檔案
- `POST /api/videos/{index}/upload_subtitle` - 上傳字幕
- `DELETE /api/videos/{index}/delete_subtitle` - 刪除字幕
- `POST /api/convert_subtitle` - 格式轉換

### 系統功能
- `POST /api/scan` - 掃描影片資料夾
- `GET /api/tags` - 獲取所有標籤
- `GET /api/tags/stats` - 標籤統計資訊

## ⚡ 效能特色

### 智慧快取機制
- **縮圖快取**：已生成的縮圖會被保存，避免重複生成
- **進度追蹤**：即時顯示縮圖生成進度
- **防重複處理**：同一影片不會同時執行多個處理任務

### 最佳化功能
- **批量處理**：支援同時處理多個影片
- **異步操作**：不阻塞使用者介面
- **記憶功能**：記住上次掃描路徑和播放位置

## 🎨 介面特色

### 現代化設計
- **響應式佈局**：適應各種螢幕尺寸
- **直觀操作**：拖拽、右鍵選單、快捷鍵支援
- **視覺回饋**：載入動畫、進度條、狀態提示

### 用戶體驗
- **快速搜尋**：即時篩選和搜尋功能
- **批量選擇**：支援 Shift 和 Ctrl 多選
- **拖拽排序**：直覺的順序調整

## 🔍 疑難排解

### 常見問題

**Q: FFmpeg 找不到？**
A: 確保 FFmpeg 已安裝且在系統 PATH 中，或將 ffmpeg.exe 放在 backend 資料夾中。

**Q: 縮圖生成失敗？**
A: 檢查影片檔案是否完整，確保有足夠的磁碟空間。

**Q: 前端無法連接後端？**
A: 確認後端服務正在運行（http://127.0.0.1:5000），檢查防火牆設定。

**Q: 字幕檔案無法識別？**
A: 確保字幕檔案與影片檔案同名且在同一目錄。

### 支援的格式
- **影片格式**：MP4, MKV, AVI, MOV
- **字幕格式**：SRT, VTT, ASS, SSA, SUB, IDX
- **縮圖格式**：PNG（320x180）

## 🤝 貢獻指南

歡迎提交 Issue 和 Pull Request！

### 開發環境設置
```bash
git clone <repository>
cd video_manager

# 設置後端開發環境
cd backend
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt

# 設置前端開發環境
cd ../frontend
npm install
npm run dev
```

## 📝 版本歷史

### v1.0.0（當前版本）
- ✅ 完整的影片管理功能
- ✅ 多時間點縮圖預覽
- ✅ 字幕檔案管理
- ✅ 標籤系統和批量操作
- ✅ 播放列表功能
- ✅ 響應式設計

## 📄 授權條款

本專案採用 MIT 授權條款。詳見 [LICENSE](LICENSE) 檔案。

## 💡 未來規劃

- [ ] 資料庫支援（SQLite/MySQL）
- [ ] 影片轉檔功能
- [ ] 雲端同步支援
- [ ] 行動應用程式
- [ ] AI 智慧標籤推薦
- [ ] 多使用者支援

---

⭐ 如果這個專案對您有幫助，請給個 Star！

🐛 發現問題？請提交 [Issue](issues)

📧 聯絡方式：[您的聯絡方式]