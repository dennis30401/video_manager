<template>
  <div v-if="show" class="modal-overlay" @click="closeModal">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h3>📊 標籤統計</h3>
        <button class="close-btn" @click="closeModal">✕</button>
      </div>
      
      <div class="modal-body">
        <div v-if="loading" class="loading">
          <div class="spinner"></div>
          <p>載入標籤統計中...</p>
        </div>
        
        <div v-else-if="error" class="error">
          <p>❌ {{ error }}</p>
          <button @click="loadTagStats" class="retry-btn">重試</button>
        </div>
        
        <div v-else class="tag-stats">
          <div class="stats-header">
            <div class="stats-info">
              <span>共 {{ tagStats.length }} 個標籤</span>
              <span>已選擇 {{ selectedTags.length }} 個</span>
            </div>
            <div class="view-controls">
              <button 
                @click="viewMode = 'grid'" 
                :class="{ active: viewMode === 'grid' }"
                class="view-btn">
                網格
              </button>
              <button 
                @click="viewMode = 'list'" 
                :class="{ active: viewMode === 'list' }"
                class="view-btn">
                列表
              </button>
            </div>
          </div>
          
          <div class="filter-controls">
            <input 
              v-model="searchQuery" 
              placeholder="搜尋標籤..." 
              class="search-input"
            />
            <select v-model="sortBy" class="sort-select">
              <option value="count">按使用次數排序</option>
              <option value="name">按名稱排序</option>
            </select>
          </div>
          
          <div class="clear-all-section" v-if="selectedTags.length > 0">
            <button @click="clearAllFilters" class="clear-all-btn">
              清除所有篩選 ({{ selectedTags.length }})
            </button>
          </div>
          
          <div :class="['tags-container', viewMode]">
            <div 
              v-for="[tag, count] in filteredTagStats" 
              :key="tag"
              :class="['tag-item', { 
                selected: selectedTags.includes(tag),
                'high-usage': count >= 10,
                'medium-usage': count >= 5 && count < 10,
                'low-usage': count < 5
              }]"
              @click="toggleTagFilter(tag)">
              <span class="tag-name">{{ tag }}</span>
              <span class="tag-count">{{ count }}</span>
              <div class="usage-bar">
                <div 
                  class="usage-fill" 
                  :style="{ width: getUsagePercentage(count) + '%' }">
                </div>
              </div>
            </div>
          </div>
          
          <div v-if="filteredTagStats.length === 0" class="no-results">
            <p>🔍 沒有找到符合的標籤</p>
          </div>
        </div>
      </div>
      
      <div class="modal-footer">
        <button @click="applyFilters" class="apply-btn">
          套用篩選 ({{ selectedTags.length }})
        </button>
        <button @click="closeModal" class="cancel-btn">取消</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import axios from 'axios';

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  currentSelectedTags: {
    type: Array,
    default: () => []
  }
});

const emit = defineEmits(['close', 'apply-filters']);

const loading = ref(false);
const error = ref('');
const tagStats = ref([]);
const selectedTags = ref([]);
const searchQuery = ref('');
const sortBy = ref('count');
const viewMode = ref('grid');

const apiBase = "http://127.0.0.1:5000";

// 計算最大使用次數，用於計算使用率條
const maxCount = computed(() => {
  if (tagStats.value.length === 0) return 1;
  return Math.max(...tagStats.value.map(([, count]) => count));
});

// 過濾和排序標籤
const filteredTagStats = computed(() => {
  let filtered = tagStats.value;
  
  // 搜尋過濾
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase().trim();
    filtered = filtered.filter(([tag]) => 
      tag.toLowerCase().includes(query)
    );
  }
  
  // 排序
  if (sortBy.value === 'count') {
    filtered = [...filtered].sort((a, b) => b[1] - a[1]);
  } else {
    filtered = [...filtered].sort((a, b) => a[0].localeCompare(b[0]));
  }
  
  return filtered;
});

// 計算使用率百分比
function getUsagePercentage(count) {
  return Math.round((count / maxCount.value) * 100);
}

// 載入標籤統計
async function loadTagStats() {
  loading.value = true;
  error.value = '';
  
  try {
    const response = await axios.get(`${apiBase}/api/tags/stats`);
    tagStats.value = response.data;
  } catch (err) {
    error.value = '載入標籤統計失敗: ' + (err.response?.data?.error || err.message);
  } finally {
    loading.value = false;
  }
}

// 切換標籤篩選
function toggleTagFilter(tag) {
  const index = selectedTags.value.indexOf(tag);
  if (index === -1) {
    selectedTags.value.push(tag);
  } else {
    selectedTags.value.splice(index, 1);
  }
}

// 清除所有篩選
function clearAllFilters() {
  selectedTags.value = [];
}

// 套用篩選
function applyFilters() {
  emit('apply-filters', [...selectedTags.value]);
  closeModal();
}

// 關閉彈窗
function closeModal() {
  emit('close');
}

// 監聽彈窗顯示狀態
watch(() => props.show, (newShow) => {
  if (newShow) {
    selectedTags.value = [...props.currentSelectedTags];
    loadTagStats();
  }
});

// 鍵盤事件
function handleKeydown(event) {
  if (event.key === 'Escape') {
    closeModal();
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown);
});
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal-content {
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  width: 90%;
  max-width: 800px;
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
  font-size: 1.4em;
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
  max-height: 60vh;
}

.loading, .error {
  text-align: center;
  padding: 40px 20px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 15px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.retry-btn {
  background: #007bff;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 10px;
}

.retry-btn:hover {
  background: #0056b3;
}

.stats-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 20px 0 15px;
  flex-wrap: wrap;
  gap: 10px;
}

.stats-info {
  display: flex;
  gap: 15px;
  font-size: 0.9em;
  color: #666;
}

.view-controls {
  display: flex;
  gap: 5px;
  background: #f8f9fa;
  border-radius: 6px;
  padding: 3px;
}

.view-btn {
  background: none;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9em;
  transition: all 0.2s;
}

.view-btn.active {
  background: white;
  color: #007bff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.filter-controls {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.search-input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  min-width: 200px;
}

.search-input:focus {
  border-color: #007bff;
  outline: none;
  box-shadow: 0 0 0 2px rgba(0,123,255,0.25);
}

.sort-select {
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  background: white;
  cursor: pointer;
}

.clear-all-section {
  margin-bottom: 20px;
}

.clear-all-btn {
  background: #dc3545;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9em;
}

.clear-all-btn:hover {
  background: #c82333;
}

.tags-container {
  margin-bottom: 20px;
}

.tags-container.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.tags-container.list .tag-item {
  margin-bottom: 8px;
}

.tag-item {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 12px 15px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

.tag-item:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  border-color: #007bff;
}

.tag-item.selected {
  background: #007bff;
  color: white;
  border-color: #007bff;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0,123,255,0.3);
}

.tag-item.high-usage {
  border-left: 4px solid #28a745;
}

.tag-item.medium-usage {
  border-left: 4px solid #ffc107;
}

.tag-item.low-usage {
  border-left: 4px solid #6c757d;
}

.tag-item.selected.high-usage,
.tag-item.selected.medium-usage,
.tag-item.selected.low-usage {
  border-left-color: rgba(255,255,255,0.8);
}

.tag-name {
  font-weight: 500;
  display: block;
  margin-bottom: 4px;
}

.tag-count {
  font-size: 0.9em;
  opacity: 0.8;
  font-weight: normal;
}

.usage-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: rgba(0,0,0,0.1);
}

.tag-item.selected .usage-bar {
  background: rgba(255,255,255,0.3);
}

.usage-fill {
  height: 100%;
  background: #007bff;
  transition: width 0.3s ease;
}

.tag-item.selected .usage-fill {
  background: rgba(255,255,255,0.6);
}

.no-results {
  text-align: center;
  padding: 40px 20px;
  color: #666;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 25px;
  border-top: 1px solid #eee;
  background: #f9f9f9;
  border-radius: 0 0 12px 12px;
}

.apply-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.apply-btn:hover {
  background: #218838;
}

.cancel-btn {
  background: #6c757d;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
}

.cancel-btn:hover {
  background: #5a6268;
}

/* 響應式設計 */
@media (max-width: 768px) {
  .modal-content {
    width: 95%;
    max-height: 95vh;
  }
  
  .modal-header, .modal-body, .modal-footer {
    padding-left: 15px;
    padding-right: 15px;
  }
  
  .tags-container.grid {
    grid-template-columns: 1fr;
  }
  
  .filter-controls {
    flex-direction: column;
  }
  
  .search-input {
    min-width: unset;
  }
}
</style>