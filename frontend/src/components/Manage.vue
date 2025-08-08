<template>
  <div>
    <button @click="toggleDarkMode">切換深色模式</button>
    <input type="text" v-model="scanPath" placeholder="掃描資料夾路徑" />
    <button @click="scan">掃描資料夾</button>
    <div>{{ sortMessage }}</div>
    <draggable v-model="videos" @end="onDragEnd" item-key="filename" class="card-container">
      <template #item="{ element, index }">
        <div class="card">
          <input type="checkbox" v-model="selectedIndexes" :value="index" :id="index" />
          <label :for="index">
            <div v-if="editIndex !== index">
              <strong>{{ element.filename }}</strong>
              <div class="tags">
                標籤：
                <span 
                  v-for="tag in (Array.isArray(element.tag) ? element.tag : [])"
                  :key="tag"
                  class="tag-display">
                  {{ tag }}
                </span>
                <span v-if="!Array.isArray(element.tag) || element.tag.length === 0" class="no-tags">無標籤</span>
              </div>
              <div>描述：{{ element.description || '（無）' }}</div>
              <div>時長：{{ element.duration || '未知' }}</div>
              <div>大小：{{ element.size || '未知' }}</div>
              <div>加入時間：{{ element.add_time || '未知' }}</div>
              <button @click="editVideo(index)">編輯</button>
              <button @click="deleteVideo(index)">刪除</button>
              <input type="file" @change="uploadThumbnail(index, $event)" accept="image/*" />
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
                <button @click="saveVideo(index)" class="save-btn">儲存</button>
                <button @click="cancelEdit" class="cancel-btn">取消</button>
              </div>
            </div>
          </label>
        </div>
      </template>
    </draggable>
    <button @click="deleteSelected">刪除所選</button>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import draggable from 'vuedraggable';
import axios from 'axios';
import TagEditor from './TagEditor.vue';

const scanPath = ref("");
const videos = ref([]);
const selectedIndexes = ref([]);
const sortMessage = ref("");
const editIndex = ref(null);
const editVideoData = reactive({ filename: "", tag: [], description: "" });

const apiBase = "http://127.0.0.1:5000";

function loadVideos() {
  axios.get(apiBase + '/api/videos').then(response => {
    videos.value = response.data;
  });
}


function scan() {
  axios.post(apiBase + '/api/scan', { path: scanPath.value }).then(() => {
    loadVideos();
  });
}

function editVideo(index) {
  editIndex.value = index;
  const video = videos.value[index];
  // 確保標籤是陣列格式
  editVideoData.filename = video.filename || '';
  editVideoData.description = video.description || '';
  editVideoData.tag = Array.isArray(video.tag) ? [...video.tag] : [];
}

function saveVideo(index) {
  axios.put(apiBase + '/api/videos/' + index, editVideoData).then(() => {
    editIndex.value = null;
    loadVideos();
  });
}

function cancelEdit() {
  editIndex.value = null;
}

function deleteVideo(index) {
  axios.delete(apiBase + '/api/videos/' + index).then(() => {
    loadVideos();
  });
}

function deleteSelected() {
  axios.post(apiBase + '/api/videos/delete_batch', { indexes: selectedIndexes.value })
    .then(() => {
      selectedIndexes.value = [];
      loadVideos();
    });
}

function uploadThumbnail(index, event) {
  const file = event.target.files[0];
  if (!file) return;
  const formData = new FormData();
  formData.append('file', file);
  axios.post(apiBase + '/api/upload_thumbnail/' + index, formData).then(() => {
    loadVideos();
  });
}

function onDragEnd() {
  axios.post(apiBase + '/api/videos/reorder', videos.value).then(() => {
    sortMessage.value = "排序已更新";
    setTimeout(() => sortMessage.value = '', 2000);
  });
}

function toggleDarkMode() {
  document.body.classList.toggle('dark-mode');
}

onMounted(() => {
  loadVideos();
  axios.get(apiBase + '/api/last_path').then(res => {
    if (res.data.path) {
      scanPath.value = res.data.path;
    }
  });
});
</script>

<style scoped>
.card-container {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.card {
  width: 22%;
  background: white;
  padding: 15px;
  margin: 5px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transition: transform 0.2s, box-shadow 0.2s;
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0,0,0,0.15);
}

.tags {
  margin: 8px 0;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 5px;
}

.tag-display {
  background: #e9ecef;
  color: #495057;
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 0.8em;
  border: 1px solid #dee2e6;
}

.no-tags {
  color: #6c757d;
  font-style: italic;
  font-size: 0.85em;
}

.edit-form {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  border: 1px solid #dee2e6;
  margin-top: 10px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  color: #495057;
  font-size: 0.9em;
}

.form-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 13px;
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
  font-size: 13px;
  min-height: 60px;
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
  margin-top: 15px;
}

.save-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
}

.save-btn:hover {
  background: #218838;
}

.cancel-btn {
  background: #6c757d;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
}

.cancel-btn:hover {
  background: #5a6268;
}

button {
  margin: 5px;
  padding: 6px 12px;
  border: 1px solid #ccc;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

button:hover {
  background: #f8f9fa;
}
</style>
