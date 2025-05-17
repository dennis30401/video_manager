<template>
  <div>
    <div>
      {{ path }}
    </div>
    <div>
      <button @click="goBack()">返回清單</button>
    </div>
    <video ref="videoPlayer" controls @keydown.left.prevent="seek(-10)" @keydown.right.prevent="seek(10)" autoplay style="width: 90%; max-width: 1300px;">
      <source :src="'http://127.0.0.1:5000/api/stream_video?path=' + encodeURIComponent(path)" type="video/mp4" />
      您的瀏覽器不支援 HTML5 視頻。
    </video>
    <div>
      <button @click="seek(-10)"><< 快退10秒</button>
      <button @click="seek(10)">快轉10秒 >></button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
const router = useRouter();
const route = useRoute();
const videoPlayer = ref(null);
const path = route.query.path || "";

function seek(seconds) {
  if (videoPlayer.value) {
    videoPlayer.value.currentTime += seconds;
  }
}

function goBack() {
    // 如果有來源頁面的 query，就帶回；否則回首頁
    if (Object.keys(route.query).length > 0) {
        const { path, ...listState } = route.query;  // 移除 path，只保留 List.vue 的狀態參數
        router.push({ path: '/', query: listState });
    } else {
        router.push({ path: '/' });
    }
}

onMounted(() => {
  const savedTime = localStorage.getItem("playback_" + path);
  if (savedTime && videoPlayer.value) {
    videoPlayer.value.currentTime = parseFloat(savedTime);
  }
  videoPlayer.value?.addEventListener("timeupdate", () => {
    localStorage.setItem("playback_" + path, videoPlayer.value.currentTime);
  });
  videoPlayer.value?.focus();
});
</script>
