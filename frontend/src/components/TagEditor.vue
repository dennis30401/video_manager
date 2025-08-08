<template>
  <div class="tag-editor">
    <div class="current-tags">
      <span 
        v-for="(tag, index) in modelValue" 
        :key="index" 
        class="tag-item"
        @click="removeTag(index)">
        {{ tag }} ✕
      </span>
      <span v-if="modelValue.length === 0" class="no-tags-hint">尚無標籤</span>
    </div>
    
    <div class="tag-input-container">
      <input 
        ref="tagInput"
        v-model="newTag" 
        @keydown.enter="addTag"
        @keydown.comma="addTagFromComma"
        @input="filterSuggestions"
        placeholder="輸入標籤，按 Enter 或逗號添加"
        class="tag-input"
      />
      <button @click="addTag" class="add-tag-btn">添加</button>
    </div>
    
    <div v-if="showSuggestions && filteredSuggestions.length > 0" class="suggestions">
      <div class="suggestions-title">建議標籤：</div>
      <span 
        v-for="suggestion in filteredSuggestions.slice(0, 10)" 
        :key="suggestion" 
        class="suggestion-item"
        @click="addSuggestion(suggestion)">
        {{ suggestion }}
      </span>
    </div>
    
    <div v-if="popularTags.length > 0" class="popular-tags">
      <div class="popular-tags-title">熱門標籤：</div>
      <span 
        v-for="[tag, count] in popularTags.slice(0, 8)" 
        :key="tag" 
        class="popular-tag"
        @click="addSuggestion(tag)"
        :title="`使用次數: ${count}`">
        {{ tag }} ({{ count }})
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import axios from 'axios';

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  }
});

const emit = defineEmits(['update:modelValue']);

const newTag = ref('');
const tagInput = ref(null);
const allTags = ref([]);
const popularTags = ref([]);
const showSuggestions = ref(false);

const apiBase = "http://127.0.0.1:5000";

// 根據輸入過濾建議標籤
const filteredSuggestions = computed(() => {
  if (!newTag.value.trim()) return [];
  const input = newTag.value.toLowerCase().trim();
  return allTags.value.filter(tag => 
    tag.toLowerCase().includes(input) && 
    !props.modelValue.includes(tag)
  );
});

// 載入所有標籤和熱門標籤
onMounted(async () => {
  try {
    const [tagsResponse, statsResponse] = await Promise.all([
      axios.get(`${apiBase}/api/tags`),
      axios.get(`${apiBase}/api/tags/stats`)
    ]);
    allTags.value = tagsResponse.data;
    popularTags.value = statsResponse.data;
  } catch (error) {
    console.error('載入標籤失敗:', error);
  }
});

function addTag() {
  const tag = newTag.value.trim();
  if (tag && !props.modelValue.includes(tag)) {
    const updatedTags = [...props.modelValue, tag];
    emit('update:modelValue', updatedTags);
    newTag.value = '';
    showSuggestions.value = false;
  }
}

function addTagFromComma(event) {
  event.preventDefault();
  addTag();
}

function removeTag(index) {
  const updatedTags = [...props.modelValue];
  updatedTags.splice(index, 1);
  emit('update:modelValue', updatedTags);
}

function addSuggestion(tag) {
  if (!props.modelValue.includes(tag)) {
    const updatedTags = [...props.modelValue, tag];
    emit('update:modelValue', updatedTags);
  }
  newTag.value = '';
  showSuggestions.value = false;
}

function filterSuggestions() {
  showSuggestions.value = newTag.value.trim().length > 0;
}

// 監聽點擊外部關閉建議
watch(newTag, (value) => {
  if (!value.trim()) {
    showSuggestions.value = false;
  }
});
</script>

<style scoped>
.tag-editor {
  position: relative;
}

.current-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-bottom: 10px;
  min-height: 24px;
}

.tag-item {
  background: #007bff;
  color: white;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.85em;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}

.tag-item:hover {
  background: #0056b3;
  transform: scale(1.05);
}

.no-tags-hint {
  color: #6c757d;
  font-style: italic;
  font-size: 0.9em;
}

.tag-input-container {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.tag-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.tag-input:focus {
  border-color: #007bff;
  outline: none;
  box-shadow: 0 0 0 2px rgba(0,123,255,0.25);
}

.add-tag-btn {
  padding: 8px 16px;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.add-tag-btn:hover {
  background: #218838;
}

.suggestions {
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 10px;
  margin-bottom: 10px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 1000;
}

.suggestions-title {
  font-size: 0.85em;
  color: #666;
  margin-bottom: 5px;
}

.suggestion-item {
  display: inline-block;
  background: #f8f9fa;
  color: #495057;
  padding: 4px 8px;
  border-radius: 8px;
  font-size: 0.85em;
  cursor: pointer;
  margin: 2px;
  transition: background 0.2s;
}

.suggestion-item:hover {
  background: #e9ecef;
}

.popular-tags {
  margin-top: 10px;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 4px;
}

.popular-tags-title {
  font-size: 0.9em;
  color: #666;
  margin-bottom: 8px;
  font-weight: bold;
}

.popular-tag {
  display: inline-block;
  background: #e9ecef;
  color: #495057;
  padding: 4px 8px;
  border-radius: 8px;
  font-size: 0.8em;
  cursor: pointer;
  margin: 2px;
  transition: all 0.2s;
}

.popular-tag:hover {
  background: #dee2e6;
  transform: translateY(-1px);
}
</style>