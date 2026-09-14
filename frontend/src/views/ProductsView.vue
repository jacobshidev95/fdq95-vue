<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/api/client'
import { useI18nStore } from '@/stores/i18n'

const route = useRoute()
const router = useRouter()
const i18n = useI18nStore()

const userId = computed(() => String(route.params.userId || ''))
const products = ref<
  Array<{
    id: string
    name: string
    description: string
    price: number
    currency: string
  }>
>([])

async function load() {
  const { data } = await api.get(`/api/products/user/${userId.value}`)
  products.value = data.products || []
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="top-bar">
      <button class="back-btn" @click="router.push(`/profile/${userId}`)">←</button>
      <span class="title">{{ i18n.t('product_list') }} — @{{ userId }}</span>
    </div>

    <p v-if="products.length === 0" class="empty">
      {{ i18n.t('no_products_yet') }}
    </p>

    <div class="grid">
      <div v-for="p in products" :key="p.id" class="card">
        <div class="thumb" />
        <div class="name">{{ p.name }}</div>
        <div class="desc">{{ p.description }}</div>
        <div class="price">{{ p.currency }} {{ p.price.toFixed(2) }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page {
  width: 100%;
  max-width: 900px;
  padding: 1rem 1.25rem 3rem;
}
.top-bar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}
.back-btn {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text);
  padding: 0.35rem 0.75rem;
  border-radius: 6px;
  cursor: pointer;
}
.title {
  color: var(--gold);
  font-weight: 700;
}
.empty {
  color: var(--text-dim);
  text-align: center;
  margin-top: 3rem;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 0.85rem;
}
.card {
  background: var(--bg-soft);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.75rem;
}
.thumb {
  height: 110px;
  background: linear-gradient(135deg, #333, #1a1a1a);
  border-radius: 6px;
  margin-bottom: 0.5rem;
}
.name {
  color: #fff;
  font-weight: 600;
  font-size: 0.9rem;
}
.desc {
  color: var(--text-dim);
  font-size: 0.78rem;
  line-height: 1.4;
  margin: 0.25rem 0 0.4rem;
}
.price {
  color: var(--gold);
  font-weight: 700;
  font-size: 0.9rem;
}
</style>