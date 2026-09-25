<script setup lang="ts">
import { ref } from 'vue'
import { useI18nStore } from '@/stores/i18n'

const i18n = useI18nStore()

const props = defineProps<{
  visible: boolean
  roomId: string
}>()

const emit = defineEmits<{
  'update:visible': [v: boolean]
  uploaded: []
}>()

const loading = ref(false)

function close() {
  emit('update:visible', false)
}

async function handleUpload() {
  // ★★★ 待实现：真正的上传逻辑
  //   - 文件选择、校验、POST /api/live/{roomId}/personal-data
  //   - 上传成功后 emit('uploaded')
  loading.value = true
  try {
    await new Promise((r) => setTimeout(r, 400))
    emit('uploaded')
    close()
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div
    v-if="visible"
    class="modal-backdrop"
    @click.self="close"
  >
    <div class="modal">
      <div class="modal-header">
        <h3>{{ i18n.t('personal_data_upload_title') }}</h3>
        <button @click="close">✕</button>
      </div>

      <div class="modal-body">
        <!--
          ★★★ 个人数据上传模板 —— 待设计
          这里后续填充：拖拽区域、字段表单、文件预览等
        -->
        <div class="placeholder">
          {{ i18n.t('personal_data_upload_placeholder') }}
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn ghost" @click="close">
          {{ i18n.t('cancel') }}
        </button>
        <button class="btn primary" :disabled="loading" @click="handleUpload">
          {{ loading ? i18n.t('publish_article_uploading') : i18n.t('upload') }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-backdrop {
  position: fixed; inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex; align-items: center; justify-content: center;
  z-index: 200;
}
.modal {
  width: 90%; max-width: 520px;
  max-height: 80vh;
  background: #111;
  border: 1px solid #333;
  border-radius: 12px;
  color: #fff;
  display: flex; flex-direction: column;
  overflow: hidden;
}
.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0.8rem 1rem;
  border-bottom: 1px solid #222;
}
.modal-header h3 { margin: 0; font-size: 1rem; }
.modal-header button {
  background: transparent; border: none; color: #fff;
  font-size: 1.1rem; cursor: pointer;
}
.modal-body {
  flex: 1 1 auto;
  padding: 1rem;
  overflow-y: auto;
  min-height: 180px;
  display: flex; align-items: center; justify-content: center;
}
.placeholder {
  color: rgba(255, 255, 255, 0.4);
  font-size: 0.85rem;
  text-align: center;
  padding: 1.5rem;
  border: 1px dashed rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  width: 100%;
}
.modal-footer {
  display: flex; justify-content: flex-end; gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-top: 1px solid #222;
}
.btn {
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
}
.btn.ghost {
  background: transparent;
  border-color: rgba(255, 255, 255, 0.2);
  color: #ddd;
}
.btn.primary {
  background: #8b5cf6;
  color: #fff;
}
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>