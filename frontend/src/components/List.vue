
<template>
  <div>
    <!-- 錯誤提示 -->
    <div v-if="error" class="error-message">
      {{ error }}
      <button @click="dismissError">關閉</button>
    </div>

    <!-- 搜尋和排序控制 -->
    <div class="controls">
      <input type="text" v-model="search" placeholder="搜尋影片..." />
      
      <select v-model="sortOrder">
        <option value="filename_asc">檔名升序</option>
        <option value="filename_desc">檔名降序</option>
        <option value="add_time_asc">加入時間升序</option>  
        <option value="add_time_desc">加入時間降序</option> 
      </select>
      
      <select v-model.number="itemsPerPage">
        <option :value="10">每頁10個</option>
        <option :value="25">每頁25個</option>
        <option :value="50">每頁50個</option>
        <option :value="100">每頁100個</option>
      </select>
      
      <button @click="clearFilters" class="clear-btn">清除所有篩選</button>
      <button @click="showTagStatsModal" class="tag-stats-btn">
        📊 標籤統計
      </button>
      <button @click="toggleBatchMode" :class="{ active: batchMode }" class="batch-mode-btn">
        📝 {{ batchMode ? '退出批量' : '批量編輯' }}
      </button>
    </div>
    
    <!-- 目前篩選的標籤 -->
    <div v-if="selectedTags.length > 0" class="selected-tags">
      <span>目前篩選標籤：</span>
      <span 
        v-for="tag in selectedTags" 
        :key="tag" 
        class="selected-tag"
        @click="removeTagFilter(tag)">
        {{ tag }} ✕
      </span>
    </div>
    
    <!-- 批量操作工具欄 -->
    <div v-if="batchMode" class="batch-toolbar">
      <div class="batch-info">
        <span>已選擇 {{ selectedVideos.length }} / {{ pagedVideos.length }} 部影片</span>
      </div>
      <div class="batch-controls">
        <button @click="selectAllVisible" class="batch-btn">全選本頁</button>
        <button @click="deselectAll" class="batch-btn">清除選擇</button>
        <button @click="showBatchTagEditor" :disabled="selectedVideos.length === 0" class="batch-btn primary">
          🏷️ 批量編輯標籤
        </button>
        <button @click="batchDeleteVideos" :disabled="selectedVideos.length === 0" class="batch-btn danger">
          🗑️ 批量刪除
        </button>
      </div>
    </div>

    <div class="grid">
      <div class="card" v-for="(video, index) in pagedVideos" :key="index" :class="{ selected: selectedVideos.includes(getGlobalIndex(video)) }">
        <!-- 批量選擇框 -->
        <div v-if="batchMode" class="batch-checkbox">
          <input 
            type="checkbox" 
            :value="getGlobalIndex(video)"
            v-model="selectedVideos"
            :id="'batch_' + index"
          />
          <label :for="'batch_' + index"></label>
        </div>
        
        <label :for="index">
          <div v-if="editIndex !== getGlobalIndex(video)">
            <img 
              :src="'http://127.0.0.1:5000/api/thumbnail?path=' + encodeURIComponent(video.thumbnail)" 
              alt="縮圖" 
              width="450px" 
              @click="batchMode ? toggleVideoSelection(getGlobalIndex(video)) : playVideo(video)"
              :class="{ 'clickable': !batchMode }" 
            />
            <strong>{{ video.filename }}</strong>
            <div class="tags">
              標籤：
              <span 
                v-for="tag in (Array.isArray(video.tag) ? video.tag : [])"
                :key="tag"
                class="tag-item"
                :class="{ active: selectedTags.includes(tag) }"
                @click.stop="toggleTagFilter(tag)">
                {{ tag }}
              </span>
              <span v-if="!Array.isArray(video.tag) || video.tag.length === 0" class="no-tags">無標籤</span>
            </div>
            <div>描述：{{ video.description || '（無）' }}</div>
            <div>加入時間：{{ video.add_time || '未知' }}</div>
            <div class="video-actions">
              <button @click="editVideo(video)" class="action-btn edit-btn">📝 編輯</button>
              <button @click="showVideoThumbnails(video)" class="action-btn thumbnail-btn">🎬 縮圖</button>
              <button @click="showVideoSubtitles(video)" class="action-btn subtitle-btn">📝 字幕</button>
              <button @click="deleteVideo(video)" class="action-btn delete-btn">🗑️ 刪除</button>
            </div>
          </div>
          <div v-else class="edit-form">
            <div class="form-group">
              <label>檔名：</label>
              <input v-model="editVideoData.filename" placeholder="檔名" class="form-input" />
            </div>
            <div class="form-group">
              <label>標籤：</label>
              <TagEditor v-model="editVideoData.tag" />
            </div>
            <div class="form-group">
              <label>描述：</label>
              <textarea v-model="editVideoData.description" placeholder="描述" class="form-textarea"></textarea>
            </div>
            <div class="form-actions">
              <button @click="saveVideo(video)" class="save-btn">儲存</button>
              <button @click="cancelEdit" class="cancel-btn">取消</button>
            </div>
          </div>
        </label>
      </div>
    </div>

    <div v-if="pagedVideos.length === 0" class="no-results">找不到符合的影片</div>

    <div v-if="totalPages > 1" class="pagination">
      <button @click="prevPage" :disabled="currentPage === 1">上一頁</button>
      <span>第 {{ currentPage }} / {{ totalPages }} 頁</span>
      <button @click="nextPage" :disabled="currentPage === totalPages">下一頁</button>
    </div>
    
    <!-- 標籤統計彈出視窗 -->
    <TagStatsModal 
      :show="showTagStats"
      :current-selected-tags="selectedTags"
      @close="closeTagStatsModal"
      @apply-filters="applyTagFilters"
    />
    
    <!-- 批量標籤編輯彈出視窗 -->
    <BatchTagEditor 
      v-if="showBatchTagModal"
      :show="showBatchTagModal"
      :selected-video-indices="selectedVideos"
      :videos="videos"
      @close="closeBatchTagModal"
      @updated="handleBatchTagUpdate"
    />
    
    <!-- 多時間點縮圖檢視器 -->
    <MultiThumbnailViewer 
      :show="showMultiThumbnailViewer"
      :video-index="selectedVideoForThumbnail"
      :video-data="selectedVideoData"
      @close="closeMultiThumbnailViewer"
      @jump-to-time="handleJumpToTime"
    />
    
    <!-- 字幕管理器 -->
    <SubtitleManager 
      :show="showSubtitleManager"
      :video-index="selectedVideoForSubtitle"
      :video-data="selectedVideoDataForSubtitle"
      @close="closeSubtitleManager"
      @subtitle-updated="handleSubtitleUpdate"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch , onUnmounted , nextTick, reactive } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import axios from 'axios';
import TagEditor from './TagEditor.vue';
import TagStatsModal from './TagStatsModal.vue';
import BatchTagEditor from './BatchTagEditor.vue';
import MultiThumbnailViewer from './MultiThumbnailViewer.vue';
import SubtitleManager from './SubtitleManager.vue';

const search = ref("");
const videos = ref([]);
const apiBase = "http://127.0.0.1:5000";
const router = useRouter();
const route = useRoute();
const error = ref("");
const selectedTags = ref([]);
const showTagStats = ref(false);
const batchMode = ref(false);
const selectedVideos = ref([]);
const showBatchTagModal = ref(false);
const showMultiThumbnailViewer = ref(false);
const selectedVideoForThumbnail = ref(-1);
const selectedVideoData = ref(null);
const showSubtitleManager = ref(false);
const selectedVideoForSubtitle = ref(-1);
const selectedVideoDataForSubtitle = ref(null);

const sortOrder = ref('add_time_desc');
const currentPage = ref(1);
const itemsPerPage = ref(10);
const restoringState = ref(false);
const editIndex = ref(null);
const editVideoData = reactive({ filename: "", tag: [], description: "" });
const allTags = ref([]);

// 讀取 query 參數
onMounted(async () => {
  try {
    restoringState.value = true;

    search.value = route.query.search || "";
    sortOrder.value = route.query.sort || "add_time_desc";
    currentPage.value = parseInt(route.query.page || "1");
    itemsPerPage.value = parseInt(route.query.items || "10");
    
    // 恢復標籤篩選
    if (route.query.tags) {
      selectedTags.value = Array.isArray(route.query.tags) 
        ? route.query.tags 
        : [route.query.tags];
    }
    
    await nextTick();

    restoringState.value = false;
    window.addEventListener('keydown', handleKeydown);
    await loadVideos();
    await loadAllTags();
  } catch (err) {
    showError('初始化失敗：' + err.message);
  }
});

onUnmounted(() => {
    window.removeEventListener('keydown', handleKeydown);
});

function getGlobalIndex(video) {
  return videos.value.findIndex(v => v.path === video.path);
}

function editVideo(video) {
  const index = videos.value.findIndex(v => v.path.toLowerCase() === video.path.toLowerCase());
  editIndex.value = index;
  const videoData = videos.value[index];
  // 確保標籤是陣列格式
  editVideoData.filename = videoData.filename || '';
  editVideoData.description = videoData.description || '';
  editVideoData.tag = Array.isArray(videoData.tag) ? [...videoData.tag] : [];
}

async function saveVideo(video) {
  try {
    const index = videos.value.findIndex(v => v.path.toLowerCase() === video.path.toLowerCase());
    await axios.put(apiBase + '/api/videos/' + index, editVideoData);
    editIndex.value = null;
    await loadVideos();
  } catch (err) {
    showError('儲存失敗：' + (err.response?.data?.error || err.message));
  }
}

function cancelEdit() {
  editIndex.value = null;
}

async function deleteVideo(video) {
  if (!confirm('確定要刪除這部影片嗎？')) return;
  
  try {
    const index = videos.value.findIndex(v => v.path.toLowerCase() === video.path.toLowerCase());
    await axios.delete(apiBase + '/api/videos/' + index);
    await loadVideos();
  } catch (err) {
    showError('刪除失敗：' + (err.response?.data?.error || err.message));
  }
}
function handleKeydown(e) {
    // 如果焦點在輸入框，跳過
    if (['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;

    if (e.key === 'ArrowRight') {
        if (currentPage.value < totalPages.value) {
            currentPage.value++;
        }
    } else if (e.key === 'ArrowLeft') {
        if (currentPage.value > 1) {
            currentPage.value--;
        }
    }
}

async function loadVideos() {
  try {
    console.log("執行 loadVideos()");
    console.log("當前搜尋條件：", search.value, sortOrder.value, currentPage.value, itemsPerPage.value);
    const response = await axios.get(apiBase + '/api/videos');
    videos.value = response.data;
    console.log("收到影片資料", response.data);
    error.value = ""; // 清除錯誤
  } catch (err) {
    console.error("取得影片失敗：", err);
    showError('載入影片清單失敗：' + (err.response?.data?.error || err.message));
  }
}

async function loadAllTags() {
  try {
    const response = await axios.get(apiBase + '/api/tags');
    allTags.value = response.data;
  } catch (err) {
    console.error('載入標籤失敗：', err);
  }
}

function handleBatchTagUpdate() {
  loadVideos();
  selectedVideos.value = [];
  showError('批量標籤編輯完成！', 'success');
}

function showError(message, type = 'error') {
  error.value = message;
  if (type === 'success') {
    // 成功訊息用綠色顯示
    const errorEl = document.querySelector('.error-message');
    if (errorEl) {
      errorEl.style.background = '#d4edda';
      errorEl.style.color = '#155724';
      errorEl.style.borderColor = '#c3e6cb';
    }
  }
  setTimeout(() => {
    error.value = "";
  }, type === 'success' ? 3000 : 5000);
}

function dismissError() {
  error.value = "";
}

function toggleTagFilter(tag) {
  const index = selectedTags.value.indexOf(tag);
  if (index === -1) {
    selectedTags.value.push(tag);
  } else {
    selectedTags.value.splice(index, 1);
  }
  currentPage.value = 1; // 重置到第一頁
  updateURL();
}

function removeTagFilter(tag) {
  const index = selectedTags.value.indexOf(tag);
  if (index !== -1) {
    selectedTags.value.splice(index, 1);
  }
  updateURL();
}

function clearFilters() {
  search.value = "";
  selectedTags.value = [];
  currentPage.value = 1;
  updateURL();
}

function updateURL() {
  const query = {
    page: currentPage.value,
    search: search.value,
    sort: sortOrder.value,
    items: itemsPerPage.value
  };
  
  if (selectedTags.value.length > 0) {
    query.tags = selectedTags.value;
  }
  
  router.replace({ path: route.path, query });
}

// 標籤統計彈出視窗相關功能
function showTagStatsModal() {
  showTagStats.value = true;
}

function closeTagStatsModal() {
  showTagStats.value = false;
}

function applyTagFilters(tags) {
  selectedTags.value = [...tags];
  currentPage.value = 1;
  updateURL();
}

// 批量操作相關功能
function toggleBatchMode() {
  batchMode.value = !batchMode.value;
  if (!batchMode.value) {
    selectedVideos.value = [];
  }
}

function toggleVideoSelection(globalIndex) {
  const index = selectedVideos.value.indexOf(globalIndex);
  if (index === -1) {
    selectedVideos.value.push(globalIndex);
  } else {
    selectedVideos.value.splice(index, 1);
  }
}

function selectAllVisible() {
  const visibleIndices = pagedVideos.value.map(video => getGlobalIndex(video));
  selectedVideos.value = [...new Set([...selectedVideos.value, ...visibleIndices])];
}

function deselectAll() {
  selectedVideos.value = [];
}

function showBatchTagEditor() {
  if (selectedVideos.value.length > 0) {
    showBatchTagModal.value = true;
  }
}

function closeBatchTagModal() {
  showBatchTagModal.value = false;
}

// 多時間點縮圖檢視器相關功能
function showVideoThumbnails(video) {
  const globalIndex = getGlobalIndex(video);
  selectedVideoForThumbnail.value = globalIndex;
  selectedVideoData.value = video;
  showMultiThumbnailViewer.value = true;
}

function closeMultiThumbnailViewer() {
  showMultiThumbnailViewer.value = false;
  selectedVideoForThumbnail.value = -1;
  selectedVideoData.value = null;
}

function handleJumpToTime(timestamp) {
  // 跳轉到播放器並設定時間點
  if (selectedVideoData.value) {
    const query = {
      path: selectedVideoData.value.path,
      timestamp: timestamp,  // 添加時間點參數
      page: currentPage.value,
      search: search.value,
      sort: sortOrder.value,
      items: itemsPerPage.value
    };
    
    if (selectedTags.value.length > 0) {
      query.tags = selectedTags.value;
    }
    
    router.push({
      path: '/player',
      query
    });
  }
}

// 字幕管理器相關功能
function showVideoSubtitles(video) {
  const globalIndex = getGlobalIndex(video);
  selectedVideoForSubtitle.value = globalIndex;
  selectedVideoDataForSubtitle.value = video;
  showSubtitleManager.value = true;
}

function closeSubtitleManager() {
  showSubtitleManager.value = false;
  selectedVideoForSubtitle.value = -1;
  selectedVideoDataForSubtitle.value = null;
}

function handleSubtitleUpdate() {
  // 字幕更新後可以重新載入影片資料或顯示提示
  showError('字幕更新成功！', 'success');
}

async function batchDeleteVideos() {
  if (selectedVideos.value.length === 0) return;
  
  const confirmMsg = `確定要刪除選中的 ${selectedVideos.value.length} 部影片嗎？這個操作不可復原！`;
  if (!confirm(confirmMsg)) return;
  
  try {
    await axios.post(`${apiBase}/api/videos/delete_batch`, {
      indexes: selectedVideos.value
    }, {
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    selectedVideos.value = [];
    await loadVideos();
    showError('批量刪除完成！', 'success');
  } catch (err) {
    showError('批量刪除失敗：' + (err.response?.data?.error || err.message));
  }
}

function playVideo(video) {
  const query = {
    path: video.path,
    page: currentPage.value,
    search: search.value,
    sort: sortOrder.value,
    items: itemsPerPage.value
  };
  
  if (selectedTags.value.length > 0) {
    query.tags = selectedTags.value;
  }
  
  router.push({
    path: '/player',
    query
  });
}

const filteredVideos = computed(() => {
    let list = Array.isArray(videos.value) ? [...videos.value] : [];
    
    // 標籤篩選
    if (selectedTags.value.length > 0) {
        list = list.filter(video => {
            const videoTags = Array.isArray(video.tag) ? video.tag : [];
            return selectedTags.value.some(tag => videoTags.includes(tag));
        });
    }
    
    // 關鍵字搜尋
    const keywordString = (search.value || '').trim().toLowerCase();
    const keywords = keywordString.split(/\s+/).filter(k => k);

    if (keywords.length > 0) {
        list = list.filter(video => {
            const filename = (video.filename || '').toLowerCase();
            const tagText = Array.isArray(video.tag) ? video.tag.join('、') : (video.tag || '');
            const desc = (video.description || '（無）').toLowerCase();
            return keywords.some(kw =>
                filename.includes(kw) || tagText.toLowerCase().includes(kw) || desc.includes(kw)
            );
        });
    }

    list.sort((a, b) => {  
      if (sortOrder.value.startsWith('filename_')) {  
          const nameA = (a.filename || "").toLowerCase();  
          const nameB = (b.filename || "").toLowerCase();  
          if (sortOrder.value === 'filename_asc') {  
              return nameA.localeCompare(nameB);  
          } else {  
              return nameB.localeCompare(nameA);  
          }  
      } else if (sortOrder.value.startsWith('add_time_')) {  
          // 如果沒有 add_time 屬性，則視為最舊的  
          const timeA = a.add_time || "1970/01/01 00:00:00";  
          const timeB = b.add_time || "1970/01/01 00:00:00";  
          if (sortOrder.value === 'add_time_asc') {  
              return timeA.localeCompare(timeB);  
          } else {  
              return timeB.localeCompare(timeA);  
          }  
      }  
      return 0;  
    });

    return list;
});



const totalPages = computed(() => {
    return Math.ceil(filteredVideos.value.length / itemsPerPage.value) || 1;
});

const pagedVideos = computed(() => {
    const totalItems = filteredVideos.value.length;

    // 如果影片列表尚未載入，不進行任何重設
    if (totalItems === 0) return [];

    const start = (currentPage.value - 1) * itemsPerPage.value;

    // 如果 start 超過，跳回第一頁
    if (start >= totalItems && currentPage.value > 1) {
        currentPage.value = 1;
        return filteredVideos.value.slice(0, itemsPerPage.value);
    }

    return filteredVideos.value.slice(start, start + itemsPerPage.value);
});



function nextPage() {
    if (currentPage.value < totalPages.value) {
        currentPage.value++;
    }
}
function prevPage() {
    if (currentPage.value > 1) {
        currentPage.value--;
    }
}

watch(
  [search, sortOrder, itemsPerPage, selectedTags],
  ([newSearch, newSort, newItems, newTags], [oldSearch, oldSort, oldItems, oldTags]) => {
    console.log("監聽觸發：", newSearch, newSort, newItems, newTags, "和", oldSearch, oldSort, oldItems, oldTags);
    console.log("restoringState = ", restoringState.value);
    if (restoringState.value) {
      console.log("正在恢復狀態，不重置頁碼");
      return;
    }

    if (newSearch !== oldSearch || newSort !== oldSort || newItems !== oldItems || 
        JSON.stringify(newTags) !== JSON.stringify(oldTags)) {
      currentPage.value = 1;
      updateURL();
    }
  },
  { flush: "post", deep: true }
);


</script>

<style scoped>
.error-message {
  background: #f8d7da;
  color: #721c24;
  padding: 10px;
  margin: 10px 0;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.error-message button {
  background: transparent;
  border: none;
  color: #721c24;
  cursor: pointer;
  font-weight: bold;
}

.controls {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 15px;
  flex-wrap: wrap;
}

.clear-btn {
  background: #dc3545;
  color: white;
  border: none;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
}

.clear-btn:hover {
  background: #c82333;
}

.selected-tags {
  margin: 10px 0;
  padding: 10px;
  background: #e9ecef;
  border-radius: 4px;
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  align-items: center;
}

.selected-tag {
  background: #007bff;
  color: white;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.85em;
  cursor: pointer;
  transition: background 0.2s;
}

.selected-tag:hover {
  background: #0056b3;
}

.tags {
  margin: 5px 0;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
}

.tag-item {
  background: #f8f9fa;
  color: #495057;
  padding: 2px 6px;
  border-radius: 8px;
  font-size: 0.85em;
  cursor: pointer;
  border: 1px solid #dee2e6;
  transition: all 0.2s;
}

.tag-item:hover {
  background: #e9ecef;
  transform: translateY(-1px);
}

.tag-item.active {
  background: #007bff;
  color: white;
  border-color: #007bff;
}

.no-tags {
  color: #6c757d;
  font-style: italic;
  font-size: 0.9em;
}

.edit-form {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  border: 1px solid #dee2e6;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  color: #495057;
}

.form-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
}

.form-input:focus {
  border-color: #007bff;
  outline: none;
  box-shadow: 0 0 0 2px rgba(0,123,255,0.25);
}

.form-textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
  min-height: 80px;
  resize: vertical;
}

.form-textarea:focus {
  border-color: #007bff;
  outline: none;
  box-shadow: 0 0 0 2px rgba(0,123,255,0.25);
}

.form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.save-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 8px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.save-btn:hover {
  background: #218838;
}

.cancel-btn {
  background: #6c757d;
  color: white;
  border: none;
  padding: 8px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.cancel-btn:hover {
  background: #5a6268;
}

.video-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
  flex-wrap: wrap;
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

.edit-btn {
  background: #17a2b8;
  color: white;
}

.edit-btn:hover {
  background: #138496;
}

.thumbnail-btn {
  background: #6f42c1;
  color: white;
}

.thumbnail-btn:hover {
  background: #5a359a;
}

.subtitle-btn {
  background: #fd7e14;
  color: white;
}

.subtitle-btn:hover {
  background: #e8590c;
}

.delete-btn {
  background: #dc3545;
  color: white;
}

.delete-btn:hover {
  background: #c82333;
}

.tag-stats-btn {
  background: #17a2b8;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 5px;
  transition: background 0.2s;
}

.tag-stats-btn:hover {
  background: #138496;
  transform: translateY(-1px);
}

.batch-mode-btn {
  background: #6f42c1;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.batch-mode-btn:hover {
  background: #5a359a;
  transform: translateY(-1px);
}

.batch-mode-btn.active {
  background: #dc3545;
  box-shadow: 0 0 0 2px rgba(220,53,69,0.3);
}

.batch-toolbar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 15px 20px;
  border-radius: 8px;
  margin: 15px 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 15px;
  box-shadow: 0 4px 15px rgba(102,126,234,0.3);
}

.batch-info {
  font-weight: 500;
  font-size: 0.95em;
}

.batch-controls {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.batch-btn {
  background: rgba(255,255,255,0.2);
  color: white;
  border: 1px solid rgba(255,255,255,0.3);
  padding: 8px 14px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9em;
  transition: all 0.2s;
  backdrop-filter: blur(10px);
}

.batch-btn:hover:not(:disabled) {
  background: rgba(255,255,255,0.3);
  transform: translateY(-1px);
}

.batch-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.batch-btn.primary {
  background: #28a745;
  border-color: #28a745;
}

.batch-btn.primary:hover:not(:disabled) {
  background: #218838;
}

.batch-btn.danger {
  background: #dc3545;
  border-color: #dc3545;
}

.batch-btn.danger:hover:not(:disabled) {
  background: #c82333;
}

.card.selected {
  border-color: #007bff;
  box-shadow: 0 0 0 3px rgba(0,123,255,0.25);
  transform: translateY(-2px);
}

.batch-checkbox {
  position: absolute;
  top: 10px;
  left: 10px;
  z-index: 10;
}

.batch-checkbox input[type="checkbox"] {
  width: 20px;
  height: 20px;
  cursor: pointer;
}

.batch-checkbox label {
  display: block;
  width: 20px;
  height: 20px;
  cursor: pointer;
  position: relative;
}

.grid .card {
  position: relative;
}

.grid .card img.clickable {
  cursor: pointer;
}

.grid .card img:not(.clickable) {
  cursor: default;
}

/* 批量模式下的卡片調整 */
.batch-mode .card {
  padding-left: 40px;
}

/* 響應式設計 */
@media (max-width: 768px) {
  .batch-toolbar {
    flex-direction: column;
    align-items: stretch;
    text-align: center;
  }
  
  .batch-controls {
    justify-content: center;
  }
  
  .batch-btn {
    flex: 1;
    min-width: 120px;
  }
}
</style>
