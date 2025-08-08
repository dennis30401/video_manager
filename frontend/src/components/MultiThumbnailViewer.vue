<template>
  <div v-if="show" class="thumbnail-viewer-overlay" @click="closeViewer">
    <div class="thumbnail-viewer-content" @click.stop>
      <div class="viewer-header">
        <h3>🎬 多時間點縮圖預覽</h3>
        <div class="video-info">
          <div class="video-title">{{ videoData?.filename || '未知影片' }}</div>
          <div class="video-meta">
            <span>時長: {{ formatDuration(videoData?.duration_seconds) }}</span>
            <span>解析度: {{ videoData?.resolution || '未知' }}</span>
            <span>大小: {{ videoData?.size || '未知' }}</span>
          </div>
        </div>
        <button class="close-btn" @click="closeViewer">✕</button>
      </div>
      
      <div class="viewer-body">
        <div v-if="loading" class="loading-section">
          <div class="loading-spinner"></div>
          <p>{{ loadingMessage || '正在生成縮圖...' }}</p>
          <div v-if="showProgress" class="progress-container">
            <div class="progress-bar-bg">
              <div class="progress-bar-fill" :style="{ width: progressPercent + '%' }"></div>
            </div>
            <div class="progress-text">{{ progressPercent }}% ({{ completedCount }}/{{ totalCount }})</div>
          </div>
        </div>
        
        <div v-else-if="error" class="error-section">
          <p>{{ error }}</p>
          <button @click="retryLoad" class="retry-btn">重試</button>
        </div>
        
        <div v-else-if="thumbnails.length === 0" class="empty-section">
          <p>暫無縮圖</p>
          <button @click="generateThumbnails" class="generate-btn">
            生成縮圖
          </button>
        </div>
        
        <div v-else class="thumbnails-grid">
          <div 
            v-for="(thumbnail, index) in thumbnails" 
            :key="index"
            :class="['thumbnail-item', { active: selectedIndex === index }]"
            @click="selectThumbnail(index, thumbnail)">
            <div class="thumbnail-wrapper">
              <img 
                :src="getThumbnailUrl(thumbnail.path)"
                :alt="`縮圖 ${index + 1}`"
                class="thumbnail-image"
                @error="handleImageError(index)" />
              <div class="thumbnail-overlay">
                <div class="timestamp">
                  {{ formatTime(thumbnail.timestamp) }}
                </div>
                <div class="thumbnail-actions">
                  <button @click.stop="jumpToTime(thumbnail)" class="jump-btn">
                    ▶️ 跳轉
                  </button>
                </div>
              </div>
            </div>
            <div class="thumbnail-info">
              <div class="time-label">{{ formatTime(thumbnail.timestamp) }}</div>
              <div class="progress-indicator">
                <div class="progress-bar" :style="{ width: getProgressWidth(thumbnail.timestamp) }"></div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 自定義縮圖生成 -->
        <div class="custom-generation">
          <div class="custom-header">
            <h4>🛠️ 自定義縮圖</h4>
            <button @click="showCustomForm = !showCustomForm" class="toggle-btn">
              {{ showCustomForm ? '隱藏' : '顯示' }}
            </button>
          </div>
          
          <div v-if="showCustomForm" class="custom-form">
            <div class="time-inputs">
              <label>指定時間點（秒）：</label>
              <div class="input-group">
                <input 
                  v-model.number="customTime" 
                  type="number" 
                  :min="0" 
                  :max="Math.floor(videoData?.duration_seconds || 0)"
                  placeholder="例如：120"
                  class="time-input" />
                <button @click="addCustomTime" class="add-btn">添加</button>
              </div>
            </div>
            
            <div v-if="customTimes.length > 0" class="custom-times">
              <div class="times-list">
                <span 
                  v-for="(time, index) in customTimes" 
                  :key="index"
                  class="time-tag">
                  {{ formatTime(time) }}
                  <button @click="removeCustomTime(index)" class="remove-time">×</button>
                </span>
              </div>
              <div class="custom-actions">
                <button @click="generateCustomThumbnails" class="generate-custom-btn">
                  生成自定義縮圖
                </button>
                <button @click="clearCustomTimes" class="clear-btn">清除</button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="viewer-footer">
        <div class="footer-info">
          <span v-if="thumbnails.length > 0">
            共 {{ thumbnails.length }} 個縮圖
          </span>
        </div>
        <div class="footer-actions">
          <button @click="refreshThumbnails" class="refresh-btn">🔄 重新生成</button>
          <button @click="closeViewer" class="close-footer-btn">關閉</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue';
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

const emit = defineEmits(['close', 'jump-to-time']);

const apiBase = "http://127.0.0.1:5000";

// 狀態
const loading = ref(false);
const error = ref('');
const thumbnails = ref([]);
const selectedIndex = ref(-1);
const showCustomForm = ref(false);
const customTime = ref('');
const customTimes = ref([]);

// 進度相關
const showProgress = ref(false);
const progressPercent = ref(0);
const loadingMessage = ref('');
const completedCount = ref(0);
const totalCount = ref(0);

// 載入多時間點縮圖
async function loadThumbnails() {
  if (props.videoIndex < 0) return;
  
  // 防止重複調用
  if (isLoading.value) {
    console.log('已經在載入中，跳過重複調用');
    return;
  }
  
  console.log('載入多時間點縮圖, videoIndex:', props.videoIndex);
  isLoading.value = true;
  loading.value = true;
  error.value = '';
  
  try {
    const response = await axios.get(`${apiBase}/api/videos/${props.videoIndex}/multi_thumbnails`);
    thumbnails.value = response.data || [];
    
    console.log('載入到的縮圖數量:', thumbnails.value.length);
    
    if (thumbnails.value.length === 0) {
      console.log('沒有縮圖，開始自動生成...');
      // 如果沒有縮圖，自動生成（顯示實時進度條）
      await generateThumbnailsWithRealTimeProgress();
    }
  } catch (err) {
    console.error('載入縮圖失敗:', err);
    error.value = '載入縮圖失敗：' + (err.response?.data?.error || err.message);
  } finally {
    loading.value = false;
    isLoading.value = false;
  }
}

// 獲取縮圖生成進度
async function fetchThumbnailProgress() {
  try {
    const response = await axios.get(`${apiBase}/api/videos/${props.videoIndex}/thumbnail_progress`);
    const progress = response.data;
    
    console.log('獲取到進度:', progress);
    
    completedCount.value = progress.completed;
    totalCount.value = progress.total;
    progressPercent.value = progress.percentage;
    loadingMessage.value = `${progress.message} (${progress.completed}/${progress.total})`;
    
    return progress;
  } catch (err) {
    console.error('獲取進度失敗:', err);
    return null;
  }
}

// 生成縮圖（帶實時進度）
async function generateThumbnailsWithRealTimeProgress(customTimestamps = null) {
  console.log('開始實時進度生成縮圖...');
  loading.value = true;
  error.value = '';
  showProgress.value = true;
  progressPercent.value = 0;
  completedCount.value = 0;
  totalCount.value = customTimestamps ? customTimestamps.length : 5;
  loadingMessage.value = customTimestamps ? 
    `開始生成 ${customTimestamps.length} 個自定義縮圖...` : 
    '沒有發現縮圖，正在自動生成 5 個縮圖...';
  
  let progressInterval = null;
  
  try {
    // 立即開始輪詢進度（先啟動輪詢再發送請求）
    progressInterval = setInterval(async () => {
      const progress = await fetchThumbnailProgress();
      console.log('輪詢進度:', progress);
    }, 500); // 每0.5秒更新一次進度
    
    console.log('發送生成縮圖請求...');
    // 開始生成縮圖
    const response = await axios.post(`${apiBase}/api/videos/${props.videoIndex}/generate_thumbnails`, 
      customTimestamps ? { timestamps: customTimestamps } : {}, {
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    console.log('生成完成回應:', response.data);
    clearInterval(progressInterval);
    progressInterval = null;
    
    // 最終更新進度顯示
    progressPercent.value = 100;
    completedCount.value = response.data.completed || response.data.thumbnails?.length || 0;
    totalCount.value = response.data.total || totalCount.value;
    loadingMessage.value = `生成完成！已生成 ${completedCount.value} 個縮圖`;
    
    thumbnails.value = response.data.thumbnails || [];
    
    // 短暫顯示完成狀態
    setTimeout(() => {
      showProgress.value = false;
    }, 2000);
    
  } catch (err) {
    console.error('生成縮圖失敗:', err);
    if (progressInterval) {
      clearInterval(progressInterval);
    }
    showProgress.value = false;
    
    // 處理 409 衝突狀態（正在生成中）
    if (err.response?.status === 409) {
      error.value = '該影片正在生成縮圖中，請稍候再試';
    } else {
      error.value = '生成縮圖失敗：' + (err.response?.data?.error || err.message);
    }
  } finally {
    loading.value = false;
  }
}

// 生成縮圖
async function generateThumbnails() {
  await generateThumbnailsWithRealTimeProgress();
}

// 生成自定義縮圖
async function generateCustomThumbnails() {
  if (customTimes.value.length === 0) return;
  
  await generateThumbnailsWithRealTimeProgress(customTimes.value);
  
  // 清除自定義時間並隱藏表單
  customTimes.value = [];
  showCustomForm.value = false;
}

// 添加自定義時間
function addCustomTime() {
  const time = customTime.value;
  if (time && time >= 0 && time <= (props.videoData?.duration_seconds || 0)) {
    if (!customTimes.value.includes(time)) {
      customTimes.value.push(time);
      customTimes.value.sort((a, b) => a - b);
    }
    customTime.value = '';
  }
}

// 移除自定義時間
function removeCustomTime(index) {
  customTimes.value.splice(index, 1);
}

// 清除自定義時間
function clearCustomTimes() {
  customTimes.value = [];
}

// 選擇縮圖
function selectThumbnail(index, thumbnail) {
  selectedIndex.value = index;
}

// 跳轉到指定時間
function jumpToTime(thumbnail) {
  emit('jump-to-time', thumbnail.timestamp);
  closeViewer();
}

// 重新生成縮圖
async function refreshThumbnails() {
  await generateThumbnails();
}

// 重試載入
async function retryLoad() {
  await loadThumbnails();
}

// 關閉檢視器
function closeViewer() {
  emit('close');
}

// 格式化時間
function formatTime(seconds) {
  if (!seconds || isNaN(seconds)) return '00:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
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

// 獲取縮圖URL
function getThumbnailUrl(path) {
  if (!path) return '';
  return `${apiBase}/api/multi_thumbnail?path=${encodeURIComponent(path)}`;
}

// 獲取進度寬度
function getProgressWidth(timestamp) {
  const duration = props.videoData?.duration_seconds || 0;
  if (duration === 0) return '0%';
  return `${(timestamp / duration) * 100}%`;
}

// 處理圖片錯誤
function handleImageError(index) {
  console.error(`縮圖 ${index + 1} 載入失敗`);
}

// 添加一個標誌來防止重複載入
const isLoading = ref(false);

// 監聽props變化
watch(() => [props.show, props.videoIndex], ([showVal, indexVal], [oldShowVal, oldIndexVal]) => {
  console.log('watch觸發:', { showVal, indexVal, oldShowVal, oldIndexVal, isLoading: isLoading.value });
  
  // 只有當對話框顯示且影片索引有效且沒有正在載入時才執行
  if (showVal && indexVal >= 0 && !isLoading.value) {
    // 防止重複載入
    if (oldShowVal !== showVal || oldIndexVal !== indexVal) {
      console.log('開始載入縮圖...');
      nextTick(() => {
        loadThumbnails();
      });
    }
  }
}, { immediate: false });
</script>

<style scoped>
.thumbnail-viewer-overlay {
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

.thumbnail-viewer-content {
  background: white;
  border-radius: 15px;
  width: 95%;
  max-width: 1200px;
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

.viewer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 25px 15px;
  border-bottom: 1px solid #eee;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 15px 15px 0 0;
}

.viewer-header h3 {
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

.viewer-body {
  flex: 1;
  overflow-y: auto;
  padding: 25px;
}

.loading-section, .error-section, .empty-section {
  text-align: center;
  padding: 40px 20px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.retry-btn, .generate-btn {
  background: #667eea;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  margin-top: 15px;
}

.retry-btn:hover, .generate-btn:hover {
  background: #5a67d8;
}

.progress-container {
  width: 100%;
  max-width: 400px;
  margin: 20px auto 0;
  text-align: center;
}

.progress-bar-bg {
  width: 100%;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 10px;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 4px;
  transition: width 0.3s ease;
  position: relative;
}

.progress-bar-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

.progress-text {
  font-size: 0.9em;
  color: #666;
  font-weight: 500;
}

.thumbnails-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.thumbnail-item {
  border: 2px solid transparent;
  border-radius: 10px;
  overflow: hidden;
  transition: all 0.3s ease;
  cursor: pointer;
  background: #f8f9fa;
}

.thumbnail-item:hover {
  border-color: #667eea;
  transform: translateY(-3px);
  box-shadow: 0 5px 20px rgba(102, 126, 234, 0.3);
}

.thumbnail-item.active {
  border-color: #28a745;
  box-shadow: 0 0 0 3px rgba(40, 167, 69, 0.25);
}

.thumbnail-wrapper {
  position: relative;
  overflow: hidden;
}

.thumbnail-image {
  width: 100%;
  height: 120px;
  object-fit: contain;
  display: block;
  background: #f8f9fa;
}

.thumbnail-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.3);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 8px;
  opacity: 0;
  transition: opacity 0.3s;
}

.thumbnail-item:hover .thumbnail-overlay {
  opacity: 1;
}

.timestamp {
  background: rgba(0,0,0,0.7);
  color: white;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.8em;
  font-weight: bold;
  align-self: flex-start;
}

.thumbnail-actions {
  align-self: center;
}

.jump-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 15px;
  cursor: pointer;
  font-size: 0.8em;
  transition: background 0.2s;
}

.jump-btn:hover {
  background: #218838;
}

.thumbnail-info {
  padding: 12px;
}

.time-label {
  font-weight: 500;
  text-align: center;
  margin-bottom: 8px;
  color: #333;
}

.progress-indicator {
  height: 4px;
  background: #e9ecef;
  border-radius: 2px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 2px;
  transition: width 0.3s ease;
}

.custom-generation {
  border-top: 1px solid #eee;
  padding-top: 20px;
}

.custom-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.custom-header h4 {
  margin: 0;
  color: #333;
}

.toggle-btn {
  background: #6c757d;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9em;
}

.toggle-btn:hover {
  background: #5a6268;
}

.custom-form {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  border: 1px solid #e9ecef;
}

.time-inputs {
  margin-bottom: 15px;
}

.time-inputs label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #555;
}

.input-group {
  display: flex;
  gap: 10px;
}

.time-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
}

.time-input:focus {
  border-color: #667eea;
  outline: none;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.25);
}

.add-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.add-btn:hover {
  background: #218838;
}

.custom-times {
  background: white;
  border-radius: 6px;
  padding: 15px;
  border: 1px solid #dee2e6;
}

.times-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 15px;
}

.time-tag {
  background: #e3f2fd;
  color: #1976d2;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.85em;
  display: flex;
  align-items: center;
  gap: 4px;
}

.remove-time {
  background: none;
  border: none;
  color: #dc3545;
  cursor: pointer;
  font-weight: bold;
  padding: 0;
  line-height: 1;
}

.remove-time:hover {
  color: #c82333;
}

.custom-actions {
  display: flex;
  gap: 10px;
}

.generate-custom-btn {
  background: #667eea;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  flex: 1;
}

.generate-custom-btn:hover {
  background: #5a67d8;
}

.clear-btn {
  background: #dc3545;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.clear-btn:hover {
  background: #c82333;
}

.viewer-footer {
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
  background: #667eea;
}

.refresh-btn:hover {
  background: #5a67d8;
}

/* 響應式設計 */
@media (max-width: 768px) {
  .thumbnail-viewer-content {
    width: 98%;
    max-height: 95vh;
  }
  
  .viewer-header {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }
  
  .video-meta {
    flex-direction: column;
    gap: 8px;
  }
  
  .thumbnails-grid {
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 15px;
  }
  
  .viewer-footer {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }
  
  .footer-actions {
    width: 100%;
    justify-content: center;
  }
}

/* 滾動條樣式 */
.viewer-body::-webkit-scrollbar {
  width: 8px;
}

.viewer-body::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.viewer-body::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.viewer-body::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>