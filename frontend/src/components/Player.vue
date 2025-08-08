<template>
  <div class="player-container">
    <!-- 播放列表側邊欄 -->
    <div :class="['playlist-sidebar', { open: showPlaylist }]">
      <div class="playlist-header">
        <h3>🎥 播放列表</h3>
        <button @click="togglePlaylist" class="close-playlist-btn">✕</button>
      </div>
      <div class="playlist-controls">
        <button @click="shuffleMode = !shuffleMode" 
                :class="{ active: shuffleMode }" 
                class="mode-btn">
          🔀 {{ shuffleMode ? '隨機' : '順序' }}
        </button>
        <button @click="autoPlay = !autoPlay" 
                :class="{ active: autoPlay }" 
                class="mode-btn">
          ⏭️ {{ autoPlay ? '自動' : '手動' }}
        </button>
      </div>
      <div class="playlist-items">
        <div 
          v-for="(video, index) in currentPlaylist" 
          :key="video.path"
          :class="['playlist-item', { active: video.path === currentVideoPath }]"
          @click="playVideoFromPlaylist(video, index)">
          <img :src="getThumbnailUrl(video.thumbnail)" 
               alt="縮圖" 
               class="playlist-thumbnail" />
          <div class="playlist-info">
            <div class="playlist-title">{{ video.filename }}</div>
            <div class="playlist-meta">
              <span class="duration">{{ video.duration }}</span>
              <span class="size">{{ video.size }}</span>
            </div>
            <div class="playlist-tags">
              <span v-for="tag in (video.tag || []).slice(0, 3)" 
                    :key="tag" 
                    class="playlist-tag">{{ tag }}</span>
            </div>
          </div>
          <div class="playlist-controls">
            <button @click.stop="removeFromPlaylist(index)" class="remove-btn">✕</button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 主要播放區域 -->
    <div class="main-player">
      <div class="video-info">
        <div class="video-title">{{ currentVideo?.filename || '未知影片' }}</div>
        <div class="video-meta">
          <span>時長: {{ currentVideo?.duration || '未知' }}</span>
          <span>大小: {{ currentVideo?.size || '未知' }}</span>
          <span>播放次數: {{ playStats.playCount }}</span>
        </div>
        <div class="video-tags">
          <span v-for="tag in (currentVideo?.tag || [])" 
                :key="tag" 
                class="video-tag">{{ tag }}</span>
        </div>
      </div>
      
      <div class="controls-top">
        <button @click="goBack()">返回清單</button>
        <button @click="togglePlaylist()">🎥 播放列表</button>
        <div class="subtitle-control">
          <button @click="toggleSubtitleMenu()" class="subtitle-btn">
            📝 字幕 {{ currentSubtitle ? '✓' : '' }}
          </button>
          <div v-if="showSubtitleMenu" class="subtitle-menu">
            <div class="subtitle-option" @click="selectSubtitle(null)">
              <span :class="{ active: !currentSubtitle }">關閉字幕</span>
            </div>
            <div 
              v-for="subtitle in availableSubtitles" 
              :key="subtitle.path"
              class="subtitle-option"
              @click="selectSubtitle(subtitle)">
              <span :class="{ active: currentSubtitle?.path === subtitle.path }">
                {{ subtitle.language }} ({{ subtitle.format }})
              </span>
            </div>
            <div v-if="availableSubtitles.length === 0" class="no-subtitles">
              無可用字幕
            </div>
          </div>
        </div>
        <button @click="toggleFullscreen()">{{ isFullscreen ? '退出全螢幕' : '全螢幕' }}</button>
      </div>
    <div class="video-wrapper" ref="videoWrapper">
      <video 
        ref="videoPlayer" 
        controls 
        autoplay 
        @dblclick="toggleFullscreen()"
        @fullscreenchange="handleFullscreenChange"
        style="width: 100%; max-width: 1800px;">
        <source :src="'http://127.0.0.1:5000/api/stream_video?path=' + encodeURIComponent(path)" type="video/mp4" />
        您的瀏覽器不支援 HTML5 視頻。
      </video>
    </div>
    <div class="controls-bottom">
      <div class="seek-controls">
        <button @click="seek(-10)"><< 快退10秒</button>
        <button @click="seek(-5)"><< 快退5秒</button>
        <button @click="seek(5)">快轉5秒 >></button>
        <button @click="seek(10)">快轉10秒 >></button>
      </div>
      <div class="speed-controls">
        <span>播放速度：</span>
        <button 
          v-for="speed in speeds" 
          :key="speed"
          @click="setSpeed(speed)"
          :class="{ active: currentSpeed === speed }">
          {{ speed }}x
        </button>
      </div>
      
      <div class="playback-controls">
        <button @click="playPrevious" :disabled="currentPlaylistIndex <= 0 && !shuffleMode">
          ⏮️ 上一部
        </button>
        <button @click="playNext" :disabled="currentPlaylistIndex >= currentPlaylist.length - 1 && !shuffleMode">
          ⏭️ 下一部
        </button>
        <button @click="addToFavorites" :class="{ active: isFavorite }">
          {{ isFavorite ? '❤️' : '🤍' }} {{ isFavorite ? '已收藏' : '收藏' }}
        </button>
      </div>
      
      <!-- 播放進度和統計 -->
      <div class="playback-info">
        <div class="progress-info">
          <span>已播放: {{ formatTime(currentTime) }} / {{ formatTime(duration) }}</span>
          <span>進度: {{ playbackProgress }}%</span>
        </div>
        <div class="session-info">
          <span>本次播放: {{ formatTime(sessionPlayTime) }}</span>
          <span>總播放時間: {{ formatTime(playStats.totalPlayTime) }}</span>
        </div>
      </div>
    </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import axios from 'axios';

const router = useRouter();
const route = useRoute();
const videoPlayer = ref(null);
const videoWrapper = ref(null);
const path = route.query.path || "";

// 播放狀態
const isFullscreen = ref(false);
const currentSpeed = ref(1);
const speeds = [0.5, 0.75, 1, 1.25, 1.5, 2];
const currentTime = ref(0);
const duration = ref(0);
const sessionPlayTime = ref(0);
const sessionStartTime = ref(Date.now());

// 播放列表相關
const showPlaylist = ref(false);
const currentPlaylist = ref([]);
const currentPlaylistIndex = ref(0);
const currentVideo = ref(null);
const shuffleMode = ref(false);
const autoPlay = ref(true);
const playHistory = ref([]);

// 統計相關
const playStats = ref({
  playCount: 0,
  totalPlayTime: 0,
  lastPlayTime: null,
  favoriteVideos: []
});

// 字幕相關
const availableSubtitles = ref([]);
const currentSubtitle = ref(null);
const showSubtitleMenu = ref(false);

const apiBase = "http://127.0.0.1:5000";

// 計算屬性
const currentVideoPath = computed(() => currentVideo.value?.path || path);
const playbackProgress = computed(() => {
  if (duration.value === 0) return 0;
  return Math.round((currentTime.value / duration.value) * 100);
});
const isFavorite = computed(() => {
  return playStats.value.favoriteVideos.includes(currentVideoPath.value);
});

function seek(seconds) {
  if (videoPlayer.value) {
    videoPlayer.value.currentTime += seconds;
  }
}

function setSpeed(speed) {
  if (videoPlayer.value) {
    videoPlayer.value.playbackRate = speed;
    currentSpeed.value = speed;
    localStorage.setItem("playback_speed_" + path, speed);
  }
}

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    if (videoWrapper.value.requestFullscreen) {
      videoWrapper.value.requestFullscreen();
    }
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen();
    }
  }
}

function handleFullscreenChange() {
  isFullscreen.value = !!document.fullscreenElement;
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
    case 'f':
    case 'F':
      event.preventDefault();
      toggleFullscreen();
      break;
    case 'Escape':
      if (document.fullscreenElement) {
        event.preventDefault();
        document.exitFullscreen();
      }
      break;
    case '-':
    case '_':
      event.preventDefault();
      const currentIndex = speeds.indexOf(currentSpeed.value);
      if (currentIndex > 0) {
        setSpeed(speeds[currentIndex - 1]);
      }
      break;
    case '=':
    case '+':
      event.preventDefault();
      const nextIndex = speeds.indexOf(currentSpeed.value);
      if (nextIndex < speeds.length - 1) {
        setSpeed(speeds[nextIndex + 1]);
      }
      break;
  }
}

onMounted(async () => {
  await loadPlaylistData();
  await loadPlaybackStats();
  await loadSubtitles();
  
  const savedTime = localStorage.getItem("playback_" + path);
  const savedSpeed = localStorage.getItem("playback_speed_" + path);
  // 檢查是否有指定的跳轉時間點
  const jumpToTimestamp = route.query.timestamp ? parseFloat(route.query.timestamp) : null;
  
  window.addEventListener('keydown', handleKeydown);
  document.addEventListener('fullscreenchange', handleFullscreenChange);
  
  await nextTick();
  
  if (videoPlayer.value) {
    videoPlayer.value.addEventListener('loadedmetadata', () => {
      duration.value = videoPlayer.value.duration || 0;
      
      // 優先使用跳轉時間點，否則使用保存的時間點
      if (jumpToTimestamp !== null && jumpToTimestamp >= 0) {
        videoPlayer.value.currentTime = jumpToTimestamp;
        // 清除URL中的timestamp參數，避免重複跳轉
        const newQuery = { ...route.query };
        delete newQuery.timestamp;
        router.replace({ path: route.path, query: newQuery });
      } else if (savedTime) {
        videoPlayer.value.currentTime = parseFloat(savedTime);
      }
    });
    
    videoPlayer.value.addEventListener('timeupdate', handleTimeUpdate);
    videoPlayer.value.addEventListener('ended', handleVideoEnded);
    videoPlayer.value.addEventListener('play', handlePlayStart);
    videoPlayer.value.addEventListener('pause', handlePlayPause);
    
    if (savedSpeed) {
      const speed = parseFloat(savedSpeed);
      setSpeed(speed);
    }
    
    videoPlayer.value.focus();
    
    // 記錄播放開始
    recordPlayStart();
  }
});

onUnmounted(() => {
  // 儲存播放統計
  savePlaybackStats();
  
  window.removeEventListener('keydown', handleKeydown);
  document.removeEventListener('fullscreenchange', handleFullscreenChange);
  
  if (videoPlayer.value) {
    videoPlayer.value.removeEventListener('timeupdate', handleTimeUpdate);
    videoPlayer.value.removeEventListener('ended', handleVideoEnded);
    videoPlayer.value.removeEventListener('play', handlePlayStart);
    videoPlayer.value.removeEventListener('pause', handlePlayPause);
  }
});

// 載入播放列表資料
async function loadPlaylistData() {
  try {
    const response = await axios.get(`${apiBase}/api/videos`);
    const allVideos = response.data;
    
    // 如果有來源查詢參數，使用相同的篩選條件建立播放列表
    if (route.query.tags || route.query.search) {
      let filteredVideos = allVideos;
      
      // 套用標籤篩選
      if (route.query.tags) {
        const tags = Array.isArray(route.query.tags) ? route.query.tags : [route.query.tags];
        filteredVideos = filteredVideos.filter(video => {
          const videoTags = Array.isArray(video.tag) ? video.tag : [];
          return tags.some(tag => videoTags.includes(tag));
        });
      }
      
      // 套用搜尋篩選
      if (route.query.search) {
        const searchTerm = route.query.search.toLowerCase();
        filteredVideos = filteredVideos.filter(video => {
          const filename = (video.filename || '').toLowerCase();
          const desc = (video.description || '').toLowerCase();
          const tagText = Array.isArray(video.tag) ? video.tag.join(' ').toLowerCase() : '';
          return filename.includes(searchTerm) || desc.includes(searchTerm) || tagText.includes(searchTerm);
        });
      }
      
      currentPlaylist.value = filteredVideos;
    } else {
      currentPlaylist.value = allVideos;
    }
    
    // 找到當前影片在播放列表中的位置
    currentPlaylistIndex.value = currentPlaylist.value.findIndex(video => video.path === path);
    if (currentPlaylistIndex.value !== -1) {
      currentVideo.value = currentPlaylist.value[currentPlaylistIndex.value];
    }
  } catch (error) {
    console.error('載入播放列表失敗:', error);
  }
}

// 載入播放統計
function loadPlaybackStats() {
  const savedStats = localStorage.getItem('playback_stats_' + path);
  if (savedStats) {
    playStats.value = { ...playStats.value, ...JSON.parse(savedStats) };
  }
  
  const globalStats = localStorage.getItem('global_playback_stats');
  if (globalStats) {
    const stats = JSON.parse(globalStats);
    playStats.value.favoriteVideos = stats.favoriteVideos || [];
  }
}

// 儲存播放統計
function savePlaybackStats() {
  localStorage.setItem('playback_stats_' + path, JSON.stringify({
    playCount: playStats.value.playCount,
    totalPlayTime: playStats.value.totalPlayTime,
    lastPlayTime: new Date().toISOString()
  }));
  
  const globalStats = {
    favoriteVideos: playStats.value.favoriteVideos
  };
  localStorage.setItem('global_playback_stats', JSON.stringify(globalStats));
}

// 時間更新處理
function handleTimeUpdate() {
  if (videoPlayer.value) {
    currentTime.value = videoPlayer.value.currentTime;
    sessionPlayTime.value = Math.floor((Date.now() - sessionStartTime.value) / 1000);
    
    // 每10秒儲存一次進度
    if (Math.floor(currentTime.value) % 10 === 0) {
      localStorage.setItem("playback_" + path, videoPlayer.value.currentTime);
    }
  }
}

// 影片結束處理
function handleVideoEnded() {
  // 更新統計
  playStats.value.totalPlayTime += sessionPlayTime.value;
  savePlaybackStats();
  
  // 自動播放下一部
  if (autoPlay.value && currentPlaylist.value.length > 1) {
    playNext();
  }
}

// 開始播放處理
function handlePlayStart() {
  playStats.value.playCount++;
  sessionStartTime.value = Date.now();
}

// 暫停播放處理
function handlePlayPause() {
  playStats.value.totalPlayTime += sessionPlayTime.value;
  sessionStartTime.value = Date.now();
}

// 記錄播放開始
function recordPlayStart() {
  playStats.value.playCount++;
  sessionStartTime.value = Date.now();
}

// 格式化時間
function formatTime(seconds) {
  if (!seconds || isNaN(seconds)) return '00:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// 播放列表相關功能
function togglePlaylist() {
  showPlaylist.value = !showPlaylist.value;
}

function playVideoFromPlaylist(video, index) {
  currentPlaylistIndex.value = index;
  currentVideo.value = video;
  
  // 保存當前播放統計
  savePlaybackStats();
  
  // 跳轉到新影片
  router.push({
    path: '/player',
    query: {
      path: video.path,
      ...route.query
    }
  });
}

function removeFromPlaylist(index) {
  currentPlaylist.value.splice(index, 1);
  if (index < currentPlaylistIndex.value) {
    currentPlaylistIndex.value--;
  } else if (index === currentPlaylistIndex.value && index >= currentPlaylist.value.length) {
    currentPlaylistIndex.value = currentPlaylist.value.length - 1;
  }
}

function playNext() {
  if (shuffleMode.value) {
    // 隨機模式：選擇隨機影片
    const availableIndices = currentPlaylist.value
      .map((_, index) => index)
      .filter(index => index !== currentPlaylistIndex.value);
    
    if (availableIndices.length > 0) {
      const randomIndex = availableIndices[Math.floor(Math.random() * availableIndices.length)];
      playVideoFromPlaylist(currentPlaylist.value[randomIndex], randomIndex);
    }
  } else {
    // 順序模式：播放下一部
    if (currentPlaylistIndex.value < currentPlaylist.value.length - 1) {
      const nextIndex = currentPlaylistIndex.value + 1;
      playVideoFromPlaylist(currentPlaylist.value[nextIndex], nextIndex);
    }
  }
}

function playPrevious() {
  if (shuffleMode.value) {
    // 隨機模式：從播放歷史中選擇
    if (playHistory.value.length > 0) {
      const previousVideo = playHistory.value.pop();
      const index = currentPlaylist.value.findIndex(v => v.path === previousVideo.path);
      if (index !== -1) {
        playVideoFromPlaylist(currentPlaylist.value[index], index);
      }
    }
  } else {
    // 順序模式：播放上一部
    if (currentPlaylistIndex.value > 0) {
      const prevIndex = currentPlaylistIndex.value - 1;
      playVideoFromPlaylist(currentPlaylist.value[prevIndex], prevIndex);
    }
  }
}

function addToFavorites() {
  const videoPath = currentVideoPath.value;
  const favorites = playStats.value.favoriteVideos;
  
  if (favorites.includes(videoPath)) {
    // 移除收藏
    playStats.value.favoriteVideos = favorites.filter(path => path !== videoPath);
  } else {
    // 添加收藏
    playStats.value.favoriteVideos.push(videoPath);
  }
  
  savePlaybackStats();
}

function getThumbnailUrl(thumbnailPath) {
  if (!thumbnailPath) return `${apiBase}/api/thumbnail?path=`;
  return `${apiBase}/api/thumbnail?path=${encodeURIComponent(thumbnailPath)}`;
}

// 字幕相關功能
async function loadSubtitles() {
  if (!currentVideo.value) return;
  
  try {
    const videoIndex = currentPlaylist.value.findIndex(v => v.path === path);
    if (videoIndex === -1) return;
    
    const response = await axios.get(`${apiBase}/api/videos/${videoIndex}/subtitles`);
    availableSubtitles.value = response.data || [];
    
    // 如果有字幕，嘗試載入保存的字幕選擇
    if (availableSubtitles.value.length > 0) {
      const savedSubtitle = localStorage.getItem(`subtitle_${path}`);
      if (savedSubtitle) {
        const subtitle = availableSubtitles.value.find(s => s.path === savedSubtitle);
        if (subtitle) {
          selectSubtitle(subtitle);
        }
      }
    }
  } catch (error) {
    console.error('載入字幕失敗:', error);
  }
}

function toggleSubtitleMenu() {
  showSubtitleMenu.value = !showSubtitleMenu.value;
}

function selectSubtitle(subtitle) {
  currentSubtitle.value = subtitle;
  showSubtitleMenu.value = false;
  
  // 更新影片的字幕軌道
  updateVideoSubtitle(subtitle);
  
  // 保存字幕選擇
  if (subtitle) {
    localStorage.setItem(`subtitle_${path}`, subtitle.path);
  } else {
    localStorage.removeItem(`subtitle_${path}`);
  }
}

function updateVideoSubtitle(subtitle) {
  if (!videoPlayer.value) return;
  
  // 移除現有的字幕軌道
  const existingTracks = videoPlayer.value.querySelectorAll('track');
  existingTracks.forEach(track => track.remove());
  
  if (subtitle) {
    // 添加新的字幕軌道
    const track = document.createElement('track');
    track.kind = 'subtitles';
    track.src = `${apiBase}/api/subtitle?path=${encodeURIComponent(subtitle.path)}`;
    track.srclang = getLanguageCode(subtitle.language);
    track.label = subtitle.language;
    track.default = true;
    
    videoPlayer.value.appendChild(track);
    
    // 確保字幕顯示
    setTimeout(() => {
      if (videoPlayer.value.textTracks.length > 0) {
        videoPlayer.value.textTracks[0].mode = 'showing';
      }
    }, 100);
  }
}

function getLanguageCode(language) {
  const languageMap = {
    '中文': 'zh',
    '繁體中文': 'zh-TW',
    '簡體中文': 'zh-CN',
    '英文': 'en',
    '日文': 'ja',
    '韓文': 'ko',
    '法文': 'fr',
    '德文': 'de',
    '西班牙文': 'es'
  };
  return languageMap[language] || 'zh';
}

// 監聽路由變化
watch(() => route.query.path, async (newPath) => {
  if (newPath && newPath !== path) {
    // 路由變化時重新載入
    await loadPlaylistData();
    await loadPlaybackStats();
  }
});

</script>

<style scoped>
.player-container {
  display: flex;
  height: 100vh;
  background: #000;
  color: white;
}

/* 播放列表側邊欄 */
.playlist-sidebar {
  width: 0;
  overflow: hidden;
  background: rgba(20, 20, 20, 0.95);
  backdrop-filter: blur(10px);
  border-right: 1px solid #333;
  transition: width 0.3s ease;
  display: flex;
  flex-direction: column;
}

.playlist-sidebar.open {
  width: 400px;
}

.playlist-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #333;
  background: rgba(0,0,0,0.3);
}

.playlist-header h3 {
  margin: 0;
  font-size: 1.2em;
}

.close-playlist-btn {
  background: none;
  border: none;
  color: #ccc;
  font-size: 18px;
  cursor: pointer;
  padding: 5px;
  border-radius: 3px;
}

.close-playlist-btn:hover {
  background: rgba(255,255,255,0.1);
  color: white;
}

.playlist-controls {
  display: flex;
  gap: 10px;
  padding: 15px 20px;
  border-bottom: 1px solid #333;
}

.mode-btn {
  background: rgba(255,255,255,0.1);
  border: 1px solid #555;
  color: white;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9em;
}

.mode-btn:hover {
  background: rgba(255,255,255,0.2);
}

.mode-btn.active {
  background: #007bff;
  border-color: #007bff;
}

.playlist-items {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.playlist-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 8px;
  background: rgba(255,255,255,0.05);
  border: 1px solid transparent;
}

.playlist-item:hover {
  background: rgba(255,255,255,0.1);
  transform: translateX(5px);
}

.playlist-item.active {
  background: rgba(0,123,255,0.3);
  border-color: #007bff;
}

.playlist-thumbnail {
  width: 80px;
  height: 45px;
  object-fit: cover;
  border-radius: 4px;
  flex-shrink: 0;
}

.playlist-info {
  flex: 1;
  min-width: 0;
}

.playlist-title {
  font-weight: 500;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 0.9em;
}

.playlist-meta {
  display: flex;
  gap: 10px;
  font-size: 0.8em;
  color: #ccc;
  margin-bottom: 4px;
}

.playlist-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.playlist-tag {
  background: rgba(255,255,255,0.15);
  padding: 2px 6px;
  border-radius: 10px;
  font-size: 0.7em;
  color: #ddd;
}

.playlist-controls {
  flex-shrink: 0;
}

.remove-btn {
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  padding: 4px;
  border-radius: 3px;
  opacity: 0;
  transition: all 0.2s;
}

.playlist-item:hover .remove-btn {
  opacity: 1;
}

.remove-btn:hover {
  background: rgba(220,53,69,0.2);
  color: #dc3545;
}

/* 主播放區域 */
.main-player {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.video-info {
  padding: 15px 20px;
  background: rgba(0,0,0,0.8);
  border-bottom: 1px solid #333;
}

.video-title {
  font-size: 1.4em;
  font-weight: bold;
  margin-bottom: 8px;
}

.video-meta {
  display: flex;
  gap: 20px;
  font-size: 0.9em;
  color: #ccc;
  margin-bottom: 8px;
}

.video-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.video-tag {
  background: rgba(0,123,255,0.2);
  color: #87ceeb;
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 0.8em;
}

.controls-top {
  padding: 15px 20px;
  background: rgba(0,0,0,0.8);
  display: flex;
  gap: 15px;
  border-bottom: 1px solid #333;
}

.video-wrapper {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #000;
  position: relative;
}

.controls-bottom {
  padding: 20px;
  background: rgba(0,0,0,0.9);
  display: flex;
  flex-direction: column;
  gap: 15px;
  border-top: 1px solid #333;
}

.seek-controls {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.speed-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.speed-controls button {
  padding: 6px 12px;
  border: 1px solid #666;
  background: rgba(255,255,255,0.1);
  color: white;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
}

.speed-controls button.active {
  background: #007bff;
  border-color: #007bff;
}

.speed-controls button:hover {
  background: rgba(255,255,255,0.2);
}

.playback-controls {
  display: flex;
  justify-content: center;
  gap: 15px;
}

.playback-controls button {
  padding: 10px 16px;
  background: rgba(255,255,255,0.1);
  border: 1px solid #555;
  color: white;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9em;
}

.playback-controls button:hover:not(:disabled) {
  background: rgba(255,255,255,0.2);
  transform: translateY(-1px);
}

.playback-controls button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.playback-controls button.active {
  background: #dc3545;
  border-color: #dc3545;
}

.playback-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  text-align: center;
  font-size: 0.9em;
  color: #ccc;
  padding: 10px 0;
  border-top: 1px solid #333;
}

.progress-info, .session-info {
  display: flex;
  justify-content: space-between;
  gap: 20px;
}

.controls-top button, .seek-controls button {
  padding: 10px 16px;
  background: rgba(255,255,255,0.1);
  color: white;
  border: 1px solid #555;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.controls-top button:hover, .seek-controls button:hover {
  background: rgba(255,255,255,0.2);
  transform: translateY(-1px);
}

/* 字幕控制 */
.subtitle-control {
  position: relative;
  display: inline-block;
}

.subtitle-btn {
  background: rgba(255,255,255,0.1);
  color: white;
  border: 1px solid #555;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  padding: 10px 16px;
}

.subtitle-btn:hover {
  background: rgba(255,255,255,0.2);
  transform: translateY(-1px);
}

.subtitle-menu {
  position: absolute;
  top: calc(100% + 5px);
  left: 0;
  background: rgba(20, 20, 20, 0.95);
  border: 1px solid #555;
  border-radius: 6px;
  min-width: 200px;
  box-shadow: 0 5px 15px rgba(0,0,0,0.5);
  z-index: 100;
  backdrop-filter: blur(10px);
}

.subtitle-option {
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.2s;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.subtitle-option:last-child {
  border-bottom: none;
}

.subtitle-option:hover {
  background: rgba(255,255,255,0.1);
}

.subtitle-option span {
  color: #ccc;
  display: block;
}

.subtitle-option span.active {
  color: #007bff;
  font-weight: 500;
}

.subtitle-option span.active::before {
  content: "✓ ";
  color: #28a745;
}

.no-subtitles {
  padding: 12px 16px;
  color: #666;
  font-style: italic;
  text-align: center;
}

/* 全螢幕樣式 */
.video-wrapper:fullscreen {
  background: #000;
}

.video-wrapper:fullscreen video {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

/* 響應式設計 */
@media (max-width: 1024px) {
  .playlist-sidebar.open {
    width: 320px;
  }
  
  .video-meta {
    flex-direction: column;
    gap: 8px;
  }
  
  .playback-controls {
    flex-wrap: wrap;
  }
}

@media (max-width: 768px) {
  .player-container {
    flex-direction: column;
  }
  
  .playlist-sidebar {
    width: 100%;
    height: 0;
    order: 2;
  }
  
  .playlist-sidebar.open {
    height: 300px;
    width: 100%;
  }
  
  .main-player {
    order: 1;
  }
  
  .controls-bottom {
    flex-wrap: wrap;
  }
  
  .seek-controls, .speed-controls, .playback-controls {
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .progress-info, .session-info {
    flex-direction: column;
    gap: 5px;
  }
}

/* 滾動條樣式 */
.playlist-items::-webkit-scrollbar {
  width: 8px;
}

.playlist-items::-webkit-scrollbar-track {
  background: rgba(255,255,255,0.1);
}

.playlist-items::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.3);
  border-radius: 4px;
}

.playlist-items::-webkit-scrollbar-thumb:hover {
  background: rgba(255,255,255,0.5);
}

/* 動畫效果 */
@keyframes slideInFromRight {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.playlist-sidebar.open {
  animation: slideInFromRight 0.3s ease-out;
}
</style>
