<template>
  <div>
    <div>
      {{ path }}
    </div>
    <div>
      <button @click="goBack()">返回清單</button>
    </div>
    <video ref="videoPlayer" controls autoplay style="width: 90%; max-width: 1800px;">
      <source :src="'http://127.0.0.1:5000/api/stream_video?path=' + encodeURIComponent(path)" type="video/mp4" />
      您的瀏覽器不支援 HTML5 視頻。
    </video>
    <div>
      <button @click="seek(-5)"><< 快退5秒</button>
      <button @click="seek(5)">快轉5秒 >></button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
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

function handleKeydown(event) {
  if (!videoPlayer.value) return;

  switch (event.key) {
    case 'ArrowLeft':
      event.preventDefault();
      seek(-5);
      break;
    case 'ArrowRight':
      event.preventDefault();
      seek(5);
      break;
    case ' ':
      event.preventDefault();
      if (videoPlayer.value.paused) {
        videoPlayer.value.play();
      } else {
        videoPlayer.value.pause();
      }
      break;
  }
}


onMounted(() => {
  const savedTime = localStorage.getItem("playback_" + path);
  window.addEventListener('keydown', handleKeydown);
  if (savedTime && videoPlayer.value) {
    videoPlayer.value.currentTime = parseFloat(savedTime);
  }
  videoPlayer.value?.addEventListener("timeupdate", () => {
    localStorage.setItem("playback_" + path, videoPlayer.value.currentTime);
  });
  videoPlayer.value?.focus();
  
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown);
});

</script>
