<script setup lang="ts">
import { useI18nStore } from '@/stores/i18n'

const i18n = useI18nStore()

defineProps<{
  roomId: string
}>()
</script>

<template>
  <div class="personal-stats-panel">
    <div class="panel-header">
      <span class="panel-icon">👤</span>
      <span class="panel-title">
        {{ i18n.t('personal_stats_title') }}
      </span>
    </div>

    <div class="panel-body">
      <!--
        ★★★ 个人数据统计模板 —— 待设计
        这里后续填充：当前用户的参与时长、贡献、积分等
      -->
      <div class="placeholder">
        {{ i18n.t('personal_stats_placeholder') }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.personal-stats-panel {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-height: 0;
  background: #111;
  border-radius: 10px;
  border: 1px solid #222;
  overflow: hidden;
}
.panel-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.45rem 0.7rem;
  background: #0d0d0d;
  border-bottom: 1px solid #222;
  font-size: 0.8rem;
  font-weight: 600;
  color: #fff;
}
.panel-icon { font-size: 0.95rem; }
.panel-title { color: #c4b5fd; }
.panel-body {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  padding: 0.5rem 0.6rem;
  display: flex;
  align-items: center;
  justify-content: center;
}
.placeholder {
  color: rgba(255, 255, 255, 0.35);
  font-size: 0.75rem;
  text-align: center;
}
</style>