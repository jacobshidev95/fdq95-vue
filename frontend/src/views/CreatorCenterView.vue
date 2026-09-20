<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useI18nStore } from '@/stores/i18n'

const router = useRouter()
const i18n = useI18nStore()

function goBack() {
  router.back()
}

function goVerifications() {
  router.push('/settings/creator/verifications')
}
function goViewStats() {
  router.push('/settings/creator/stats')
}
function goAudience() {
  router.push('/settings/creator/audience')
}
function goRevenue() {
  router.push('/settings/creator/revenue')
}
function goTools() {
  router.push('/settings/creator/tools')
}
</script>

<template>
  <div class="creator-page">
    <!-- 顶栏 -->
    <header class="top-bar">
      <button class="back-btn" @click="goBack">‹</button>
      <h1 class="page-title">{{ i18n.t('creator_center') }}</h1>
      <span class="spacer" />
    </header>

    <div class="scroll-body">
      <!-- 卡片 1：账号认证 -->
      <section class="card">
        <button class="row-item" @click="goVerifications">
          <span class="row-icon">✅</span>
          <div class="row-text">
            <div class="row-title">{{ i18n.t('creator_verifications') }}</div>
            <div class="row-sub">{{ i18n.t('creator_verifications_sub') }}</div>
          </div>
          <span class="row-arrow">›</span>
        </button>

        <!-- 卡片 2：浏览数据统计 -->
        <button class="row-item" @click="goViewStats">
          <span class="row-icon">📊</span>
          <div class="row-text">
            <div class="row-title">{{ i18n.t('creator_view_stats') }}</div>
            <div class="row-sub">{{ i18n.t('creator_view_stats_sub') }}</div>
          </div>
          <span class="row-arrow">›</span>
        </button>

        <!-- 卡片 3：观众分析 -->
        <button class="row-item" @click="goAudience">
          <span class="row-icon">👥</span>
          <div class="row-text">
            <div class="row-title">{{ i18n.t('creator_audience') }}</div>
            <div class="row-sub">{{ i18n.t('creator_audience_sub') }}</div>
          </div>
          <span class="row-arrow">›</span>
        </button>

        <!-- 卡片 4：收入详情 -->
        <button class="row-item" @click="goRevenue">
          <span class="row-icon">💰</span>
          <div class="row-text">
            <div class="row-title">{{ i18n.t('creator_revenue') }}</div>
            <div class="row-sub">{{ i18n.t('creator_revenue_sub') }}</div>
          </div>
          <span class="row-arrow">›</span>
        </button>

        <!-- 卡片 5：服务工具 -->
        <button class="row-item" @click="goTools">
          <span class="row-icon">🛠️</span>
          <div class="row-text">
            <div class="row-title">{{ i18n.t('creator_tools') }}</div>
            <div class="row-sub">{{ i18n.t('creator_tools_sub') }}</div>
          </div>
          <span class="row-arrow">›</span>
        </button>
      </section>
    </div>
  </div>
</template>

<style scoped>
.creator-page {
  display: flex;
  flex-direction: column;
  width: 100%;
  min-height: 100vh;
  background: #000;
  color: #fff;
}

.top-bar {
  display: flex;
  align-items: center;
  padding: 0.8rem 1rem;
  background: #000;
  position: sticky;
  top: 0;
  z-index: 10;
  flex-shrink: 0;
}
.back-btn {
  background: transparent;
  border: none;
  color: #fff;
  font-size: 2rem;
  line-height: 1;
  cursor: pointer;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  padding: 0;
}
.back-btn:hover { background: rgba(255, 255, 255, 0.08); }
.page-title {
  flex: 1;
  text-align: right;
  margin: 0;
  font-size: 1rem;
  font-weight: 500;
}
.spacer { width: 36px; }

.scroll-body {
  flex: 1 1 auto;
  padding: 0 0.75rem 2rem;
  overflow-y: auto;
}

.card {
  background: #1a1a1a;
  border-radius: 12px;
  overflow: hidden;
}

.row-item {
  display: flex;
  align-items: center;
  width: 100%;
  background: transparent;
  border: none;
  color: #fff;
  padding: 1rem 1rem;
  cursor: pointer;
  text-align: left;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  transition: background 0.15s;
}
.row-item:hover { background: rgba(255, 255, 255, 0.05); }
.row-item:last-child { border-bottom: none; }

.row-icon {
  font-size: 1.35rem;
  width: 32px;
  flex-shrink: 0;
  text-align: center;
  margin-right: 0.75rem;
}
.row-text {
  flex: 1;
  min-width: 0;
}
.row-title {
  color: #fff;
  font-size: 0.95rem;
  font-weight: 500;
}
.row-sub {
  color: rgba(255, 255, 255, 0.45);
  font-size: 0.78rem;
  margin-top: 0.15rem;
}
.row-arrow {
  color: rgba(255, 255, 255, 0.4);
  font-size: 1.1rem;
  margin-left: 0.5rem;
  flex-shrink: 0;
}
</style>