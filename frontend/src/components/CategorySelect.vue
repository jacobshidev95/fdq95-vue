<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

interface Props {
  modelValue: string | null
  storageKey?: string
  placeholder?: string
  disabled?: boolean
  includeAll?: boolean
  allLabel?: string
}

const props = withDefaults(defineProps<Props>(), {
  storageKey: 'fdq95_category_last',
  placeholder: 'Select category',
  disabled: false,
  includeAll: false,
  allLabel: '全部',
})

const emit = defineEmits<{
  'update:modelValue': [v: string | null]
}>()

const CATEGORIES: { value: string; key: string }[] = [
  { value: 'medical',       key: 'Medical' },
  { value: 'health',        key: 'Health' },
  { value: 'education',     key: 'Education' },
  { value: 'entertainment', key: 'Entertainment' },
  { value: 'travel',        key: 'Travel' },
  { value: 'food',          key: 'Food' },
  { value: 'clothing',      key: 'Clothing' },
  { value: 'industry',      key: 'Industry' },
  { value: 'tech',          key: 'Technology' },
  { value: 'iot',           key: 'IoT' },
  { value: 'life',          key: 'Life' },
  { value: 'ai',            key: 'AI' },
]

const open = ref(false)
const query = ref('')
const rootEl = ref<HTMLElement | null>(null)

const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return CATEGORIES
  return CATEGORIES.filter(
    c =>
      c.key.toLowerCase().includes(q) ||
      c.value.toLowerCase().includes(q)
  )
})

const currentLabel = computed(() => {
  if (props.modelValue == null || props.modelValue === '') {
    return props.includeAll ? props.allLabel : props.placeholder
  }
  const c = CATEGORIES.find(x => x.value === props.modelValue)
  return c ? c.key : props.modelValue
})

function pick(v: string | null) {
  emit('update:modelValue', v)
  if (v) localStorage.setItem(props.storageKey, v)
  else localStorage.removeItem(props.storageKey)
  open.value = false
  query.value = ''
}

function toggle() {
  if (props.disabled) return
  open.value = !open.value
}

function onDocClick(e: MouseEvent) {
  if (!rootEl.value) return
  if (!rootEl.value.contains(e.target as Node)) open.value = false
}

onMounted(() => {
  if ((props.modelValue == null || props.modelValue === '') && !props.includeAll) {
    const saved = localStorage.getItem(props.storageKey)
    if (saved) emit('update:modelValue', saved)
  }
  document.addEventListener('click', onDocClick)
})

onBeforeUnmount(() => document.removeEventListener('click', onDocClick))
</script>

<template>
  <div ref="rootEl" class="cat-select" :class="{ disabled }">
    <button
      type="button"
      class="cat-trigger"
      :disabled="disabled"
      @click="toggle"
    >
      <span class="cat-label">{{ currentLabel }}</span>
      <span class="cat-arrow">▾</span>
    </button>
    <div v-if="open" class="cat-panel">
      <input
        v-model="query"
        class="cat-search"
        type="text"
        placeholder="Search category…"
        @click.stop
      />
      <ul class="cat-list">
        <li
          v-if="includeAll"
          class="cat-item"
          :class="{ active: !modelValue }"
          @click="pick(null)"
        >{{ allLabel }}</li>
        <li
          v-for="c in filtered"
          :key="c.value"
          class="cat-item"
          :class="{ active: modelValue === c.value }"
          @click="pick(c.value)"
        >{{ c.key }}</li>
        <li v-if="filtered.length === 0" class="cat-empty">Not Match</li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.cat-select { position: relative; width: 100%; }
.cat-trigger {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 8px;
  color: #fff;
  padding: 0.45rem 0.7rem;
  font-size: 0.9rem;
  cursor: pointer;
}
.cat-trigger:hover { border-color: #8b5cf6; }
.cat-select.disabled .cat-trigger { opacity: 0.5; cursor: not-allowed; }
.cat-arrow { opacity: 0.6; font-size: 0.8rem; }
.cat-panel {
  position: absolute;
  top: calc(100% + 4px);
  left: 0; right: 0;
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 8px;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.5);
  z-index: 50;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.cat-search {
  border: none;
  border-bottom: 1px solid #333;
  background: transparent;
  color: #fff;
  padding: 0.5rem 0.7rem;
  font-size: 0.85rem;
  outline: none;
}
.cat-list {
  list-style: none;
  margin: 0; padding: 0.3rem 0;
  overflow-y: auto;
  max-height: 220px;
}
.cat-item {
  padding: 0.45rem 0.7rem;
  font-size: 0.88rem;
  cursor: pointer;
  color: #fff;
}
.cat-item:hover { background: rgba(139, 92, 246, 0.15); }
.cat-item.active {
  background: rgba(139, 92, 246, 0.25);
  color: #c4b5fd;
  font-weight: 600;
}
.cat-empty {
  padding: 0.5rem 0.7rem;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.4);
  text-align: center;
}
</style>