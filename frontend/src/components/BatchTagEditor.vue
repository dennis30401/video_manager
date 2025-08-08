<template>
  <div v-if="show" class="modal-overlay" @click="closeModal">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h3>🏷️ 批量標籤編輯</h3>
        <button class="close-btn" @click="closeModal">✕</button>
      </div>
      
      <div class="modal-body">
        <div class="selected-videos-info">
          <h4>選中的影片 ({{ selectedVideoIndices.length }})</h4>
          <div class="video-list">
            <div 
              v-for="(video, index) in selectedVideos" 
              :key="video.path"
              class="video-item">
              <img :src="getThumbnailUrl(video.thumbnail)" 
                   alt="縮圖" 
                   class="video-thumbnail" />
              <div class="video-info">
                <div class="video-title">{{ video.filename }}</div>
                <div class="current-tags">
                  <span v-for="tag in video.tag" :key="tag" class="current-tag">{{ tag }}</span>
                  <span v-if="!video.tag || video.tag.length === 0" class="no-tags">無標籤</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="batch-operations">
          <div class="operation-section">
            <h4>🏷️ 標籤操作</h4>
            <div class="operation-tabs">
              <button 
                v-for="op in operations" 
                :key="op.id"
                @click="currentOperation = op.id"
                :class="{ active: currentOperation === op.id }"
                class="tab-btn">
                {{ op.icon }} {{ op.label }}
              </button>
            </div>
            
            <div class="operation-content">
              <!-- 添加標籤 -->
              <div v-if="currentOperation === 'add'" class="operation-panel">
                <div class="operation-desc">為選中的所有影片添加標籤</div>
                <TagEditor v-model="operationTags" placeholder="輸入要添加的標籤" />
              </div>
              
              <!-- 移除標籤 -->
              <div v-if="currentOperation === 'remove'" class="operation-panel">
                <div class="operation-desc">從選中的影片中移除指定標籤</div>
                <div class="common-tags-section">
                  <div class="common-tags-title">所選影片的共同標籤：</div>
                  <div class="common-tags">
                    <span 
                      v-for="tag in commonTags" 
                      :key="tag"
                      @click="toggleOperationTag(tag)"
                      :class="{ selected: operationTags.includes(tag) }"
                      class="common-tag">
                      {{ tag }}
                    </span>
                    <span v-if="commonTags.length === 0" class="no-common-tags">無共同標籤</span>
                  </div>
                </div>
                <TagEditor v-model="operationTags" placeholder="或手動輸入要移除的標籤" />
              </div>
              
              <!-- 替換標籤 -->
              <div v-if="currentOperation === 'replace'" class="operation-panel">
                <div class="operation-desc">完全替換選中影片的所有標籤</div>
                <TagEditor v-model="operationTags" placeholder="輸入新的標籤（將完全替換現有標籤）" />
              </div>
              
              <!-- 合併標籤 -->
              <div v-if="currentOperation === 'merge'" class="operation-panel">
                <div class="operation-desc">將多個標籤合併為一個</div>
                <div class="merge-section">
                  <div class="merge-row">
                    <label>要合併的標籤：</label>
                    <div class="merge-tags">
                      <input 
                        v-model="mergeFromTag" 
                        placeholder="輸入要被替換的標籤"
                        class="merge-input" />
                    </div>
                  </div>
                  <div class="merge-arrow">↓</div>
                  <div class="merge-row">
                    <label>合併成：</label>
                    <input 
                      v-model="mergeToTag" 
                      placeholder="輸入目標標籤"
                      class="merge-input" />
                  </div>
                </div>\n              </div>
            </div>
          </div>
          
          <div class="preview-section">
            <h4>📋 操作預覽</h4>
            <div class="preview-content">
              <div v-if="previewResults.length > 0" class="preview-list">
                <div 
                  v-for="result in previewResults.slice(0, 5)" 
                  :key="result.filename"
                  class="preview-item">
                  <div class="preview-filename">{{ result.filename }}</div>
                  <div class="preview-changes">
                    <div class="tag-changes">
                      <span class="before-tags">
                        <strong>原本：</strong>
                        <span v-for="tag in result.before" :key="tag" class="preview-tag before">{{ tag }}</span>
                        <span v-if="result.before.length === 0" class="no-tags">無標籤</span>
                      </span>
                      <span class="arrow">→</span>
                      <span class="after-tags">
                        <strong>修改後：</strong>
                        <span v-for="tag in result.after" :key="tag" class="preview-tag after">{{ tag }}</span>
                        <span v-if="result.after.length === 0" class="no-tags">無標籤</span>
                      </span>
                    </div>
                  </div>
                </div>
                <div v-if="previewResults.length > 5" class="preview-more">
                  ...還有 {{ previewResults.length - 5 }} 個影片
                </div>
              </div>
              <div v-else class="no-preview">
                <p>請選擇操作類型並設定標籤以查看預覽</p>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="modal-footer">
        <div class="operation-summary">
          <span v-if="previewResults.length > 0">
            將影響 {{ previewResults.length }} 部影片
          </span>
        </div>
        <div class="footer-buttons">
          <button @click="executeOperation" 
                  :disabled="!canExecute || isExecuting" 
                  class="execute-btn">
            <span v-if="isExecuting">執行中...</span>
            <span v-else>執行操作</span>
          </button>
          <button @click="closeModal" class="cancel-btn">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import axios from 'axios';
import TagEditor from './TagEditor.vue';

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  selectedVideoIndices: {
    type: Array,
    default: () => []
  },
  videos: {
    type: Array,
    default: () => []
  }
});

const emit = defineEmits(['close', 'updated']);

const apiBase = "http://127.0.0.1:5000";

// 操作類型
const operations = [
  { id: 'add', label: '添加標籤', icon: '➕' },
  { id: 'remove', label: '移除標籤', icon: '➖' },
  { id: 'replace', label: '替換標籤', icon: '🔄' },
  { id: 'merge', label: '合併標籤', icon: '🔗' }
];

const currentOperation = ref('add');
const operationTags = ref([]);
const mergeFromTag = ref('');
const mergeToTag = ref('');
const isExecuting = ref(false);

// 計算屬性
const selectedVideos = computed(() => {
  return props.selectedVideoIndices.map(index => props.videos[index]).filter(Boolean);
});

const commonTags = computed(() => {
  if (selectedVideos.value.length === 0) return [];
  
  const allTags = selectedVideos.value.map(video => video.tag || []);
  if (allTags.length === 0) return [];
  
  return allTags[0].filter(tag => 
    allTags.every(videoTags => videoTags.includes(tag))
  );
});

const previewResults = computed(() => {
  return selectedVideos.value.map(video => {
    const before = [...(video.tag || [])];
    let after = [];
    
    switch (currentOperation.value) {
      case 'add':
        after = [...new Set([...before, ...operationTags.value])];
        break;
      case 'remove':
        after = before.filter(tag => !operationTags.value.includes(tag));
        break;
      case 'replace':
        after = [...operationTags.value];
        break;
      case 'merge':
        if (mergeFromTag.value && mergeToTag.value) {
          after = before.map(tag => 
            tag === mergeFromTag.value ? mergeToTag.value : tag
          );
          after = [...new Set(after)]; // 去重
        } else {
          after = before;
        }
        break;
      default:
        after = before;
    }
    
    return {
      filename: video.filename,
      before,
      after
    };
  }).filter(result => 
    // 只顯示有變化的項目
    JSON.stringify(result.before) !== JSON.stringify(result.after)
  );
});

const canExecute = computed(() => {
  if (isExecuting.value) return false;
  if (selectedVideos.value.length === 0) return false;
  
  switch (currentOperation.value) {
    case 'add':
    case 'remove':
    case 'replace':
      return operationTags.value.length > 0;
    case 'merge':
      return mergeFromTag.value.trim() && mergeToTag.value.trim();
    default:
      return false;
  }
});

// 方法
function closeModal() {
  emit('close');
}

function toggleOperationTag(tag) {
  const index = operationTags.value.indexOf(tag);
  if (index === -1) {
    operationTags.value.push(tag);
  } else {
    operationTags.value.splice(index, 1);
  }
}

function getThumbnailUrl(thumbnailPath) {
  if (!thumbnailPath) return `${apiBase}/api/thumbnail?path=`;
  return `${apiBase}/api/thumbnail?path=${encodeURIComponent(thumbnailPath)}`;
}

async function executeOperation() {
  if (!canExecute.value) return;
  
  isExecuting.value = true;
  
  try {
    const operations = previewResults.value.map((result, index) => {
      const videoIndex = props.selectedVideoIndices[selectedVideos.value.findIndex(v => v.filename === result.filename)];
      return {
        index: videoIndex,
        newTags: result.after
      };
    });
    
    // 批量更新標籤
    await Promise.all(operations.map(async (op) => {
      const video = props.videos[op.index];
      const updateData = {
        filename: video.filename,
        description: video.description || '',
        tag: op.newTags
      };
      
      return axios.put(`${apiBase}/api/videos/${op.index}`, updateData);
    }));
    
    emit('updated');
    closeModal();
    
  } catch (error) {
    console.error('批量操作失敗:', error);
    alert('操作失敗: ' + (error.response?.data?.error || error.message));
  } finally {
    isExecuting.value = false;
  }
}

// 監聽操作類型變化，重置操作標籤
watch(currentOperation, () => {
  operationTags.value = [];
  mergeFromTag.value = '';
  mergeToTag.value = '';
});
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
  backdrop-filter: blur(4px);
}

.modal-content {
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  width: 95%;
  max-width: 1000px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
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

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 25px 15px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  color: #333;
  font-size: 1.5em;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
  padding: 5px;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: #f5f5f5;
  color: #666;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 0 25px;
  max-height: calc(90vh - 140px);
}

.selected-videos-info {
  margin: 20px 0;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 15px;
  background: #f8f9fa;
}

.selected-videos-info h4 {
  margin: 0 0 15px 0;
  color: #495057;
}

.video-list {
  max-height: 200px;
  overflow-y: auto;
}

.video-item {
  display: flex;
  gap: 12px;
  padding: 8px;
  border-radius: 6px;
  margin-bottom: 8px;
  background: white;
  border: 1px solid #dee2e6;
}

.video-thumbnail {
  width: 60px;
  height: 34px;
  object-fit: cover;
  border-radius: 4px;
  flex-shrink: 0;
}

.video-info {
  flex: 1;
  min-width: 0;
}

.video-title {
  font-size: 0.9em;
  font-weight: 500;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.current-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.current-tag {
  background: #e3f2fd;
  color: #1976d2;
  padding: 2px 6px;
  border-radius: 10px;
  font-size: 0.75em;
}

.no-tags {
  color: #999;
  font-style: italic;
  font-size: 0.8em;
}

.batch-operations {
  margin: 20px 0;
}

.operation-section {
  margin-bottom: 30px;
}

.operation-section h4 {
  margin: 0 0 15px 0;
  color: #333;
}

.operation-tabs {
  display: flex;
  gap: 5px;
  margin-bottom: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  padding: 5px;
}

.tab-btn {
  flex: 1;
  background: none;
  border: none;
  padding: 10px 15px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9em;
  color: #666;
}

.tab-btn:hover {
  background: rgba(255,255,255,0.8);
}

.tab-btn.active {
  background: white;
  color: #007bff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  font-weight: 500;
}

.operation-panel {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  border: 1px solid #e9ecef;
}

.operation-desc {
  margin-bottom: 15px;
  color: #666;
  font-size: 0.95em;
}

.common-tags-section {
  margin: 15px 0;
}

.common-tags-title {
  font-size: 0.9em;
  color: #555;
  margin-bottom: 8px;
}

.common-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.common-tag {
  background: #fff3cd;
  color: #856404;
  padding: 4px 10px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.85em;
  border: 1px solid #ffeaa7;
}

.common-tag:hover {
  background: #ffc107;
  color: white;
}

.common-tag.selected {
  background: #dc3545;
  color: white;
  border-color: #dc3545;
}

.no-common-tags {
  color: #999;
  font-style: italic;
}

.merge-section {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.merge-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.merge-row label {
  min-width: 100px;
  font-weight: 500;
  color: #555;
}

.merge-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

.merge-input:focus {
  border-color: #007bff;
  outline: none;
  box-shadow: 0 0 0 2px rgba(0,123,255,0.25);
}

.merge-arrow {
  text-align: center;
  font-size: 1.2em;
  color: #007bff;
  font-weight: bold;
}

.preview-section {
  border-top: 1px solid #eee;
  padding-top: 20px;
}

.preview-section h4 {
  margin: 0 0 15px 0;
  color: #333;
}

.preview-content {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 15px;
  border: 1px solid #e9ecef;
}

.preview-list {
  max-height: 250px;
  overflow-y: auto;
}

.preview-item {
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 10px;
}

.preview-filename {
  font-weight: 500;
  margin-bottom: 8px;
  color: #333;
}

.tag-changes {
  font-size: 0.9em;
}

.before-tags, .after-tags {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 4px 0;
  flex-wrap: wrap;
}

.preview-tag {
  padding: 2px 6px;
  border-radius: 10px;
  font-size: 0.8em;
}

.preview-tag.before {
  background: #f8d7da;
  color: #721c24;
}

.preview-tag.after {
  background: #d4edda;
  color: #155724;
}

.arrow {
  color: #007bff;
  font-weight: bold;
  margin: 0 8px;
}

.preview-more {
  text-align: center;
  color: #666;
  font-style: italic;
  margin-top: 10px;
}

.no-preview {
  text-align: center;
  color: #999;
  padding: 20px;
}

.modal-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 25px;
  border-top: 1px solid #eee;
  background: #f9f9f9;
  border-radius: 0 0 12px 12px;
}

.operation-summary {
  color: #666;
  font-size: 0.9em;
}

.footer-buttons {
  display: flex;
  gap: 12px;
}

.execute-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s;
}

.execute-btn:hover:not(:disabled) {
  background: #218838;
}

.execute-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.cancel-btn {
  background: #6c757d;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 6px;
  cursor: pointer;
}

.cancel-btn:hover {
  background: #5a6268;
}

/* 響應式設計 */
@media (max-width: 768px) {
  .modal-content {
    width: 98%;
    max-height: 95vh;
  }
  
  .operation-tabs {
    flex-direction: column;
  }
  
  .tab-btn {
    flex: none;
  }
  
  .merge-row {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .merge-row label {
    min-width: unset;
  }
  
  .modal-footer {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }
  
  .footer-buttons {
    width: 100%;
    justify-content: center;
  }
}

/* 滾動條樣式 */
.video-list::-webkit-scrollbar,
.preview-list::-webkit-scrollbar {
  width: 6px;
}

.video-list::-webkit-scrollbar-track,
.preview-list::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.video-list::-webkit-scrollbar-thumb,
.preview-list::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.video-list::-webkit-scrollbar-thumb:hover,
.preview-list::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>