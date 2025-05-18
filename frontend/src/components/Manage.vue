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
              <strong>{{ element.filename }}</strong> | 標籤：{{ Array.isArray(element.tag) ? element.tag.join('、') : '' }}
              <div>描述：{{ element.description || '（無）' }}</div>
              <div>時長：{{ element.duration || '未知' }}</div>
              <div>大小：{{ element.size || '未知' }}</div>
              <div>加入時間：{{ element.add_time || '未知' }}</div>
              <button @click="editVideo(index)">編輯</button>
              <button @click="deleteVideo(index)">刪除</button>
              <input type="file" @change="uploadThumbnail(index, $event)" accept="image/*" />
            </div>
            <div v-else>
              <input v-model="editVideoData.filename" placeholder="檔名" />
              <input v-model="editVideoData.tag" placeholder="請輸入標籤" />
              <input v-model="editVideoData.description" placeholder="描述" />
              <button @click="saveVideo(index)">儲存</button>
              <button @click="cancelEdit">取消</button>
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

const scanPath = ref("");
const videos = ref([]);
const selectedIndexes = ref([]);
const sortMessage = ref("");
const editIndex = ref(null);
const editVideoData = reactive({ filename: "", tag: "", description: "" });

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
  Object.assign(editVideoData, videos.value[index]);
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
