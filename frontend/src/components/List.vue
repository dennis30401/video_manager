
<template>
  <div>
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

    <div class="grid">
      <div class="card" v-for="(video, index) in pagedVideos" :key="index">
        <label :for="index">
          <div v-if="editIndex !== getGlobalIndex(video)">
            <img :src="'http://127.0.0.1:5000/api/thumbnail?path=' + encodeURIComponent(video.thumbnail)" alt="縮圖" width="450px" @click="playVideo(video)" />
            <strong>{{ video.filename }}</strong>
            <div>標籤：{{ Array.isArray(video.tag) ? video.tag.join('、') : '' }}</div>
            <div>描述：{{ video.description || '（無）' }}</div>
            <div>加入時間：{{ video.add_time || '未知' }}</div>
            <button @click="editVideo(video)">編輯</button>
            <button @click="deleteVideo(video)">刪除</button>
          </div>
          <div v-else>
            <input v-model="editVideoData.filename" placeholder="檔名" />
            <input v-model="editVideoData.tag" placeholder="請輸入標籤" />
            <input v-model="editVideoData.description" placeholder="描述" />
            <button @click="saveVideo(video)">儲存</button>
            <button @click="cancelEdit">取消</button>
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch , onUnmounted , nextTick, reactive } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import axios from 'axios';

const search = ref("");
const videos = ref([]);
const apiBase = "http://127.0.0.1:5000";
const router = useRouter();
const route = useRoute();

const sortOrder = ref('add_time_desc');
const currentPage = ref(1);
const itemsPerPage = ref(10);
const restoringState = ref(false);
const editIndex = ref(null);
const editVideoData = reactive({ filename: "", tag: [], description: "" });

// 讀取 query 參數
onMounted(async () => {

  restoringState.value = true;

  search.value = route.query.search || "";
  sortOrder.value = route.query.sort || "add_time_desc";
  currentPage.value = parseInt(route.query.page || "1");
  itemsPerPage.value = parseInt(route.query.items || "10");
  
  await nextTick();

  restoringState.value = false;
  window.addEventListener('keydown', handleKeydown);
  loadVideos();
  
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
  Object.assign(editVideoData, videos.value[index]);
}

function saveVideo(video) {
  const index = videos.value.findIndex(v => v.path.toLowerCase() === video.path.toLowerCase());
  axios.put(apiBase + '/api/videos/' + index, editVideoData).then(() => {
    editIndex.value = null;
    loadVideos();
  });
}

function cancelEdit() {
  editIndex.value = null;
}

function deleteVideo(video) {
  const index = videos.value.findIndex(v => v.path.toLowerCase() === video.path.toLowerCase());
  axios.delete(apiBase + '/api/videos/' + index).then(() => {
    loadVideos();
  });
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

function loadVideos() {
  console.log("執行 loadVideos()");
  console.log("當前搜尋條件：", search.value, sortOrder.value, currentPage.value, itemsPerPage.value);
  axios.get(apiBase + '/api/videos').then(response => {
    videos.value = response.data;
    console.log("收到影片資料", response.data);
  }).catch(error => {
    console.error("取得影片失敗：", error);
  });
}

function playVideo(video) {
  router.push({
    path: '/player',
    query: {
      path: video.path,
      page: currentPage.value,
      search: search.value,
      sort: sortOrder.value,
      items: itemsPerPage.value
    }
  });
}

const filteredVideos = computed(() => {
    let list = Array.isArray(videos.value) ? [...videos.value] : [];
    const keywordString = (search.value || '').trim().toLowerCase();

    // 把搜尋字串依空白切割成多個關鍵字
    const keywords = keywordString.split(/\s+/).filter(k => k);

    list = list.filter(video => {
        const filename = (video.filename || '').toLowerCase();
        const tagText = Array.isArray(video.tag) ? video.tag.join('、') : (video.tag || '');
        const desc = (video.description || '（無）').toLowerCase();
        // OR 條件：至少有一個關鍵字符合
        return keywords.length === 0 || keywords.some(kw =>
            filename.includes(kw) || video.tag.includes(kw) || desc.includes(kw)
        );
    });

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
  [search, sortOrder, itemsPerPage],
  ([newSearch, newSort, newItems], [oldSearch, oldSort, oldItems]) => {
    console.log("監聽觸發：", newSearch, newSort, newItems, "和", oldSearch, oldSort, oldItems);
    console.log("restoringState = ", restoringState.value);
    if (restoringState.value) {
      console.log("正在恢復狀態，不重置頁碼");
      return;
    }

    if (newSearch !== oldSearch || newSort !== oldSort || newItems !== oldItems) {
      currentPage.value = 1;
    }
  },
  { flush: "post" }
);


</script>
