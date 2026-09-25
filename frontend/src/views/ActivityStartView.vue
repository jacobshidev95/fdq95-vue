<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { liveApi } from '@/api/live'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const errorMsg = ref('')

onMounted(async () => {
  try {
    if (!auth.user) await auth.fetchMe()
    const title = localStorage.getItem('fdq95_activity_title') || ''
    const category =
      localStorage.getItem('fdq95_activity_category') || 'activity'
    const s = await liveApi.start(title, category)
    router.replace(`/activity/${s.room_id}/host`)
  } catch (e: any) {
    errorMsg.value = e?.response?.data?.detail || '启动活动失败'
  }
})
</script>

<template>
  <div class="start-activity">
    <div v-if="!errorMsg">正在准备活动…</div>
    <div v-else class="err">
      <p>{{ errorMsg }}</p>
      <button @click="router.push('/activity')">返回</button>
    </div>
  </div>
</template>

<style scoped>
.start-activity {
  display: flex; align-items: center; justify-content: center;
  height: 100vh; color: #fff; background: #000;
}
.err { display: flex; flex-direction: column; align-items: center; gap: 1rem; }
.err button {
  background: #8b5cf6; color: #fff; border: none;
  padding: 0.6rem 1.2rem; border-radius: 8px; cursor: pointer;
}
</style>