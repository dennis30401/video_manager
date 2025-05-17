<template>
  <div>
    <h1>影片管理系統</h1>
    <nav>
      <router-link to="/manage">影片管理</router-link> |
      <router-link to="/list">影片清單</router-link>
    </nav>
    <router-view></router-view>
  </div>
</template>

<script setup>
// 無需 script，router 控制內容
</script>

<style scoped>
nav {
  margin-bottom: 20px;
}
</style>
