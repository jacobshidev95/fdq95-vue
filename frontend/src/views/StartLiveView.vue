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
    const title = localStorage.getItem('fdq95_live_title') || ''
    const category = localStorage.getItem('fdq95_live_category') || null
    const s = await liveApi.start(title, category)
    router.replace(`/live/${s.room_id}/host`)
  } catch (e: any) {
    errorMsg.value = e?.response?.data?.detail || '启动直播失败'
  }
})
</script>

<template>
  <div class="start-live">
    <div v-if="!errorMsg">正在准备直播间…</div>
    <div v-else class="err">
      <p>{{ errorMsg }}</p>
      <button @click="router.push('/live')">返回大厅</button>
    </div>
  </div>
</template>

<style scoped>
.start-live {
  display: flex; align-items: center; justify-content: center;
  height: 100vh; color: #fff; background: #000;
}
.err { display: flex; flex-direction: column; align-items: center; gap: 1rem; }
.err button {
  background: #8b5cf6; color: #fff; border: none;
  padding: 0.6rem 1.2rem; border-radius: 8px; cursor: pointer;
}
</style>