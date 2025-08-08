<template>
  <div v-if="show" class="subtitle-manager-overlay" @click="closeManager">
    <div class="subtitle-manager-content" @click.stop>
      <div class="manager-header">
        <h3>📝 字幕檔案管理</h3>
        <div class="video-info">
          <div class="video-title">{{ videoData?.filename || '未知影片' }}</div>
          <div class="video-meta">
            <span>時長: {{ formatDuration(videoData?.duration_seconds) }}</span>
            <span>大小: {{ videoData?.size || '未知' }}</span>
          </div>
        </div>
        <button class="close-btn" @click="closeManager">✕</button>
      </div>
      
      <div class="manager-body">
        <div v-if="loading" class="loading-section">
          <div class="loading-spinner"></div>
          <p>載入字幕檔案...</p>
        </div>
        
        <div v-else-if="error" class="error-section">
          <p>{{ error }}</p>
          <button @click="loadSubtitles" class="retry-btn">重試</button>
        </div>
        
        <div v-else>
          <!-- 現有字幕檔案 -->
          <div class="subtitles-section">
            <div class="section-header">
              <h4>🎬 現有字幕</h4>
              <span class="subtitle-count">{{ subtitles.length }} 個檔案</span>
            </div>
            
            <div v-if="subtitles.length === 0" class="no-subtitles">
              <p>尚無字幕檔案</p>
              <div class="no-subtitles-icon">📄</div>
            </div>
            
            <div v-else class="subtitles-list">
              <div 
                v-for="(subtitle, index) in subtitles" 
                :key="index"
                class="subtitle-item">
                <div class="subtitle-info">
                  <div class="subtitle-header">
                    <div class="subtitle-name">{{ subtitle.filename }}</div>
                    <div class="subtitle-badges">
                      <span class="format-badge" :class="subtitle.format.toLowerCase()">
                        {{ subtitle.format }}
                      </span>
                      <span class="language-badge">{{ subtitle.language }}</span>
                    </div>
                  </div>
                  <div class="subtitle-meta">
                    <span>大小: {{ subtitle.size }}</span>
                    <span>格式: {{ subtitle.format }}</span>
                    <span>語言: {{ subtitle.language }}</span>
                  </div>
                </div>
                <div class="subtitle-actions">
                  <button @click="previewSubtitle(subtitle)" class="action-btn preview-btn">
                    👁️ 預覽
                  </button>
                  <button @click="downloadSubtitle(subtitle)" class="action-btn download-btn">
                    📥 下載
                  </button>
                  <button @click="showConvertDialog(subtitle)" class="action-btn convert-btn">
                    🔄 轉換
                  </button>
                  <button @click="deleteSubtitle(subtitle, index)" class="action-btn delete-btn">
                    🗑️ 刪除
                  </button>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 上傳新字幕 -->
          <div class="upload-section">
            <div class="section-header">
              <h4>📤 上傳字幕</h4>
            </div>
            
            <div class="upload-area">
              <div class="upload-form">
                <div class="form-group">
                  <label>選擇字幕檔案:</label>
                  <input 
                    type="file" 
                    @change="handleFileSelect"
                    accept=".srt,.vtt,.ass,.ssa,.sub,.idx"
                    class="file-input"
                    ref="fileInput" />
                </div>
                
                <div class="form-group">
                  <label>語言標識 (可選):</label>
                  <select v-model="selectedLanguage" class="language-select">
                    <option value="">自動檢測</option>
                    <option value="zh">中文</option>
                    <option value="cht">繁體中文</option>
                    <option value="chs">簡體中文</option>
                    <option value="en">英文</option>
                    <option value="ja">日文</option>
                    <option value="ko">韓文</option>
                    <option value="fr">法文</option>
                    <option value="de">德文</option>
                    <option value="es">西班牙文</option>
                  </select>
                </div>
                
                <div class="upload-info" v-if="selectedFile">
                  <div class="selected-file">
                    <span class="file-name">{{ selectedFile.name }}</span>
                    <span class="file-size">({{ formatFileSize(selectedFile.size) }})</span>
                  </div>
                </div>
                
                <button 
                  @click="uploadSubtitle" 
                  :disabled="!selectedFile || uploading"
                  class="upload-btn">
                  <span v-if="uploading">上傳中...</span>
                  <span v-else>📤 上傳字幕</span>
                </button>
              </div>
              
              <div class="supported-formats">
                <h5>支援格式:</h5>
                <div class="format-list">
                  <span class="format-tag">SRT</span>
                  <span class="format-tag">VTT</span>
                  <span class="format-tag">ASS</span>
                  <span class="format-tag">SSA</span>
                  <span class="format-tag">SUB</span>
                  <span class="format-tag">IDX</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="manager-footer">
        <div class="footer-info">
          <span>支援多種字幕格式，自動檢測語言</span>
        </div>
        <div class="footer-actions">
          <button @click="refreshSubtitles" class="refresh-btn">🔄 重新載入</button>
          <button @click="closeManager" class="close-footer-btn">關閉</button>
        </div>
      </div>
    </div>
    
    <!-- 字幕預覽彈窗 -->
    <div v-if="showPreview" class="preview-overlay" @click="closePreview">
      <div class="preview-content" @click.stop>
        <div class="preview-header">
          <h4>字幕預覽: {{ selectedPreviewSubtitle?.filename }}</h4>
          <button @click="closePreview" class="close-preview-btn">✕</button>
        </div>
        <div class="preview-body">
          <div v-if="previewLoading" class="loading-preview">載入中...</div>
          <div v-else-if="previewError" class="preview-error">{{ previewError }}</div>
          <pre v-else class="preview-text">{{ previewContent }}</pre>
        </div>
      </div>
    </div>
    
    <!-- 格式轉換彈窗 -->
    <div v-if="showConvertModal" class="convert-overlay" @click="closeConvertModal">
      <div class="convert-content" @click.stop>
        <div class="convert-header">
          <h4>字幕格式轉換</h4>
          <button @click="closeConvertModal" class="close-convert-btn">✕</button>
        </div>
        <div class="convert-body">
          <div class="convert-info">
            <p>來源檔案: {{ convertSubtitle?.filename }}</p>
            <p>目前格式: {{ convertSubtitle?.format }}</p>
          </div>
          <div class="convert-options">
            <label>轉換為:</label>
            <select v-model="targetFormat" class="format-select">
              <option v-if="convertSubtitle?.format !== 'VTT'" value="vtt">VTT (Web Video Text Tracks)</option>
              <option v-if="convertSubtitle?.format !== 'SRT'" value="srt">SRT (SubRip Text)</option>
            </select>
          </div>
          <div class="convert-actions">
            <button @click="performConversion" :disabled="converting" class="convert-execute-btn">
              <span v-if="converting">轉換中...</span>
              <span v-else>🔄 執行轉換</span>
            </button>
            <button @click="closeConvertModal" class="convert-cancel-btn">取消</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue';
import axios from 'axios';

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  videoIndex: {
    type: Number,
    required: true
  },
  videoData: {
    type: Object,
    default: () => ({})
  }
});

const emit = defineEmits(['close', 'subtitle-updated']);

const apiBase = "http://127.0.0.1:5000";

// 狀態
const loading = ref(false);
const error = ref('');
const subtitles = ref([]);
const selectedFile = ref(null);
const selectedLanguage = ref('');
const uploading = ref(false);

// 預覽相關
const showPreview = ref(false);
const selectedPreviewSubtitle = ref(null);
const previewContent = ref('');
const previewLoading = ref(false);
const previewError = ref('');

// 轉換相關
const showConvertModal = ref(false);
const convertSubtitle = ref(null);
const targetFormat = ref('');
const converting = ref(false);

const fileInput = ref(null);

// 載入字幕檔案
async function loadSubtitles() {
  if (props.videoIndex < 0) return;
  
  loading.value = true;
  error.value = '';
  
  try {
    const response = await axios.get(`${apiBase}/api/videos/${props.videoIndex}/subtitles`);
    subtitles.value = response.data || [];
  } catch (err) {
    console.error('載入字幕失敗:', err);
    error.value = '載入字幕失敗：' + (err.response?.data?.error || err.message);
  } finally {
    loading.value = false;
  }
}

// 檔案選擇
function handleFileSelect(event) {
  const files = event.target.files;
  if (files && files.length > 0) {
    selectedFile.value = files[0];
  }
}

// 上傳字幕
async function uploadSubtitle() {
  if (!selectedFile.value) return;
  
  uploading.value = true;
  
  try {
    const formData = new FormData();
    formData.append('file', selectedFile.value);
    if (selectedLanguage.value) {
      formData.append('language', selectedLanguage.value);
    }
    
    const response = await axios.post(
      `${apiBase}/api/videos/${props.videoIndex}/upload_subtitle`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    );
    
    // 重新載入字幕列表
    await loadSubtitles();
    
    // 清除選擇
    selectedFile.value = null;
    selectedLanguage.value = '';
    if (fileInput.value) {
      fileInput.value.value = '';
    }
    
    emit('subtitle-updated');
    
  } catch (err) {
    console.error('上傳字幕失敗:', err);
    error.value = '上傳字幕失敗：' + (err.response?.data?.error || err.message);
  } finally {
    uploading.value = false;
  }
}

// 刪除字幕
async function deleteSubtitle(subtitle, index) {
  if (!confirm(`確定要刪除字幕「${subtitle.filename}」嗎？`)) return;
  
  try {
    await axios.delete(`${apiBase}/api/videos/${props.videoIndex}/delete_subtitle`, {
      data: { subtitle_path: subtitle.path },
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    // 從列表中移除
    subtitles.value.splice(index, 1);
    emit('subtitle-updated');
    
  } catch (err) {
    console.error('刪除字幕失敗:', err);
    error.value = '刪除字幕失敗：' + (err.response?.data?.error || err.message);
  }
}

// 預覽字幕
async function previewSubtitle(subtitle) {
  selectedPreviewSubtitle.value = subtitle;
  showPreview.value = true;
  previewLoading.value = true;
  previewError.value = '';
  
  try {
    const response = await axios.get(`${apiBase}/api/subtitle?path=${encodeURIComponent(subtitle.path)}`);
    previewContent.value = response.data;
  } catch (err) {
    console.error('載入字幕預覽失敗:', err);
    previewError.value = '載入預覽失敗';
  } finally {
    previewLoading.value = false;
  }
}

// 下載字幕
function downloadSubtitle(subtitle) {
  const url = `${apiBase}/api/subtitle?path=${encodeURIComponent(subtitle.path)}`;
  const link = document.createElement('a');
  link.href = url;
  link.download = subtitle.filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// 顯示轉換對話框
function showConvertDialog(subtitle) {
  convertSubtitle.value = subtitle;
  showConvertModal.value = true;
  
  // 設定目標格式
  if (subtitle.format === 'SRT') {
    targetFormat.value = 'vtt';
  } else {
    targetFormat.value = 'srt';
  }
}

// 執行格式轉換
async function performConversion() {
  if (!convertSubtitle.value || !targetFormat.value) return;
  
  converting.value = true;
  
  try {
    const response = await axios.post(`${apiBase}/api/convert_subtitle`, {
      source_path: convertSubtitle.value.path,
      target_format: targetFormat.value
    }, {
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    // 重新載入字幕列表
    await loadSubtitles();
    
    closeConvertModal();
    emit('subtitle-updated');
    
  } catch (err) {
    console.error('轉換字幕失敗:', err);
    error.value = '轉換字幕失敗：' + (err.response?.data?.error || err.message);
  } finally {
    converting.value = false;
  }
}

// 重新載入字幕
async function refreshSubtitles() {
  await loadSubtitles();
}

// 關閉管理器
function closeManager() {
  emit('close');
}

// 關閉預覽
function closePreview() {
  showPreview.value = false;
  selectedPreviewSubtitle.value = null;
  previewContent.value = '';
}

// 關閉轉換彈窗
function closeConvertModal() {
  showConvertModal.value = false;
  convertSubtitle.value = null;
  targetFormat.value = '';
}

// 格式化時長
function formatDuration(seconds) {
  if (!seconds || isNaN(seconds)) return '未知';
  const hours = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  
  if (hours > 0) {
    return `${hours}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// 格式化檔案大小
function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 監聽props變化
import { watch } from 'vue';

watch(() => props.show, (newVal) => {
  if (newVal && props.videoIndex >= 0) {
    nextTick(() => {
      loadSubtitles();
    });
  }
});

watch(() => props.videoIndex, (newVal) => {
  if (newVal >= 0 && props.show) {
    loadSubtitles();
  }
});
</script>

<style scoped>
.subtitle-manager-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
  backdrop-filter: blur(5px);
}

.subtitle-manager-content {
  background: white;
  border-radius: 15px;
  width: 95%;
  max-width: 1000px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  animation: modalSlideIn 0.3s ease-out;
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-50px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.manager-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 25px 15px;
  border-bottom: 1px solid #eee;
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
  color: white;
  border-radius: 15px 15px 0 0;
}

.manager-header h3 {
  margin: 0;
  font-size: 1.5em;
}

.video-info {
  flex: 1;
  margin: 0 20px;
  text-align: center;
}

.video-title {
  font-weight: bold;
  margin-bottom: 5px;
}

.video-meta {
  display: flex;
  justify-content: center;
  gap: 15px;
  font-size: 0.9em;
  opacity: 0.9;
}

.close-btn {
  background: rgba(255,255,255,0.2);
  border: none;
  color: white;
  font-size: 24px;
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.close-btn:hover {
  background: rgba(255,255,255,0.3);
}

.manager-body {
  flex: 1;
  overflow-y: auto;
  padding: 25px;
}

.loading-section, .error-section {
  text-align: center;
  padding: 40px 20px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #28a745;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.retry-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  margin-top: 15px;
}

.retry-btn:hover {
  background: #218838;
}

.subtitles-section {
  margin-bottom: 40px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid #e9ecef;
}

.section-header h4 {
  margin: 0;
  color: #333;
  font-size: 1.3em;
}

.subtitle-count {
  background: #e9ecef;
  color: #6c757d;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.9em;
}

.no-subtitles {
  text-align: center;
  padding: 40px 20px;
  color: #6c757d;
  background: #f8f9fa;
  border-radius: 8px;
  border: 2px dashed #dee2e6;
}

.no-subtitles-icon {
  font-size: 3em;
  margin-top: 15px;
  opacity: 0.5;
}

.subtitles-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.subtitle-item {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 10px;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.2s;
}

.subtitle-item:hover {
  box-shadow: 0 3px 15px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.subtitle-info {
  flex: 1;
}

.subtitle-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.subtitle-name {
  font-weight: bold;
  color: #333;
}

.subtitle-badges {
  display: flex;
  gap: 8px;
}

.format-badge, .language-badge {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 0.8em;
  font-weight: 500;
}

.format-badge {
  background: #e3f2fd;
  color: #1976d2;
}

.format-badge.srt {
  background: #e8f5e8;
  color: #2e7d32;
}

.format-badge.vtt {
  background: #fff3e0;
  color: #f57c00;
}

.format-badge.ass, .format-badge.ssa {
  background: #fce4ec;
  color: #c2185b;
}

.language-badge {
  background: #f3e5f5;
  color: #7b1fa2;
}

.subtitle-meta {
  display: flex;
  gap: 15px;
  color: #6c757d;
  font-size: 0.9em;
}

.subtitle-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85em;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 4px;
}

.action-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

.preview-btn {
  background: #17a2b8;
  color: white;
}

.preview-btn:hover {
  background: #138496;
}

.download-btn {
  background: #28a745;
  color: white;
}

.download-btn:hover {
  background: #218838;
}

.convert-btn {
  background: #6f42c1;
  color: white;
}

.convert-btn:hover {
  background: #5a359a;
}

.delete-btn {
  background: #dc3545;
  color: white;
}

.delete-btn:hover {
  background: #c82333;
}

.upload-section {
  border-top: 1px solid #eee;
  padding-top: 30px;
}

.upload-area {
  background: #f8f9fa;
  border-radius: 10px;
  padding: 25px;
  border: 1px solid #dee2e6;
}

.upload-form {
  margin-bottom: 25px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #555;
}

.file-input, .language-select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ced4da;
  border-radius: 6px;
  font-size: 14px;
}

.file-input:focus, .language-select:focus {
  border-color: #28a745;
  outline: none;
  box-shadow: 0 0 0 2px rgba(40, 167, 69, 0.25);
}

.upload-info {
  background: white;
  border-radius: 6px;
  padding: 15px;
  border: 1px solid #dee2e6;
  margin-bottom: 20px;
}

.selected-file {
  display: flex;
  align-items: center;
  gap: 10px;
}

.file-name {
  font-weight: 500;
  color: #333;
}

.file-size {
  color: #6c757d;
  font-size: 0.9em;
}

.upload-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  width: 100%;
  transition: background 0.2s;
}

.upload-btn:hover:not(:disabled) {
  background: #218838;
}

.upload-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.supported-formats {
  border-top: 1px solid #dee2e6;
  padding-top: 20px;
}

.supported-formats h5 {
  margin: 0 0 15px 0;
  color: #555;
}

.format-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.format-tag {
  background: #e9ecef;
  color: #495057;
  padding: 4px 10px;
  border-radius: 10px;
  font-size: 0.85em;
  font-weight: 500;
}

.manager-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 25px;
  border-top: 1px solid #eee;
  background: #f9f9f9;
  border-radius: 0 0 15px 15px;
}

.footer-info {
  color: #666;
  font-size: 0.9em;
}

.footer-actions {
  display: flex;
  gap: 12px;
}

.refresh-btn, .close-footer-btn {
  background: #6c757d;
  color: white;
  border: none;
  padding: 10px 16px;
  border-radius: 6px;
  cursor: pointer;
}

.refresh-btn:hover {
  background: #5a6268;
}

.refresh-btn {
  background: #28a745;
}

.refresh-btn:hover {
  background: #218838;
}

/* 預覽彈窗 */
.preview-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2100;
}

.preview-content {
  background: white;
  border-radius: 10px;
  width: 90%;
  max-width: 800px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #eee;
}

.preview-header h4 {
  margin: 0;
  color: #333;
}

.close-preview-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #666;
}

.close-preview-btn:hover {
  color: #333;
}

.preview-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  max-height: 60vh;
}

.loading-preview {
  text-align: center;
  padding: 40px;
  color: #666;
}

.preview-error {
  color: #dc3545;
  text-align: center;
  padding: 40px;
}

.preview-text {
  font-family: monospace;
  font-size: 0.9em;
  line-height: 1.6;
  white-space: pre-wrap;
  background: #f8f9fa;
  padding: 20px;
  border-radius: 6px;
  border: 1px solid #dee2e6;
  margin: 0;
}

/* 轉換彈窗 */
.convert-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2100;
}

.convert-content {
  background: white;
  border-radius: 10px;
  width: 90%;
  max-width: 500px;
  display: flex;
  flex-direction: column;
}

.convert-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #eee;
  background: #6f42c1;
  color: white;
  border-radius: 10px 10px 0 0;
}

.convert-header h4 {
  margin: 0;
}

.close-convert-btn {
  background: none;
  border: none;
  color: white;
  font-size: 20px;
  cursor: pointer;
}

.close-convert-btn:hover {
  opacity: 0.8;
}

.convert-body {
  padding: 25px;
}

.convert-info {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 15px;
  margin-bottom: 20px;
  border: 1px solid #dee2e6;
}

.convert-info p {
  margin: 5px 0;
  color: #555;
}

.convert-options {
  margin-bottom: 25px;
}

.convert-options label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #555;
}

.format-select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ced4da;
  border-radius: 6px;
  font-size: 14px;
}

.format-select:focus {
  border-color: #6f42c1;
  outline: none;
  box-shadow: 0 0 0 2px rgba(111, 66, 193, 0.25);
}

.convert-actions {
  display: flex;
  gap: 15px;
}

.convert-execute-btn, .convert-cancel-btn {
  flex: 1;
  padding: 12px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s;
}

.convert-execute-btn {
  background: #6f42c1;
  color: white;
  border: none;
}

.convert-execute-btn:hover:not(:disabled) {
  background: #5a359a;
}

.convert-execute-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.convert-cancel-btn {
  background: #6c757d;
  color: white;
  border: none;
}

.convert-cancel-btn:hover {
  background: #5a6268;
}

/* 響應式設計 */
@media (max-width: 768px) {
  .subtitle-manager-content {
    width: 98%;
    max-height: 95vh;
  }
  
  .manager-header {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }
  
  .video-meta {
    flex-direction: column;
    gap: 8px;
  }
  
  .subtitle-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .subtitle-actions {
    width: 100%;
    justify-content: space-around;
  }
  
  .action-btn {
    flex: 1;
    text-align: center;
  }
  
  .manager-footer {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }
  
  .footer-actions {
    width: 100%;
    justify-content: center;
  }
}
</style>