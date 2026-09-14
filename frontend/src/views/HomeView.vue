<script setup lang="ts">
import LeftVideoTicker from '@/components/LeftVideoTicker.vue'
import CenterContent from '@/components/CenterContent.vue'
import RightVideoTicker from '@/components/RightVideoTicker.vue'
</script>

<template>
  <div class="home-layout">
    <LeftVideoTicker class="panel-left" />
    <CenterContent class="panel-center" />
    <RightVideoTicker class="panel-right" />
  </div>
</template>

<style scoped>
.home-layout {
  flex: 1;
  display: grid;
  grid-template-columns: 25% 50% 25%;
  width: 100%;
  min-height: 0;
  overflow: hidden;
}
.home-layout > * {
  min-width: 0;
  min-height: 0;
  overflow-y: auto;
}

/* ---------- Responsive: stack on narrow screens ---------- */
@media (max-width: 900px) {
  .home-layout {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto auto;
    overflow: visible;
  }
  .panel-left,
  .panel-right {
    max-height: 320px;
  }
}
</style>