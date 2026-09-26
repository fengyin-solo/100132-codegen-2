<template>
  <div class="app-shell">
    <aside class="app-side">
      <h1 class="app-title">污水处理厂工艺管理平台</h1>
      <nav class="nav-list">
        <RouterLink v-for="item in navItems" :key="item.path" :to="item.path" class="nav-item">
          {{ item.label }}
        </RouterLink>
      </nav>
    </aside>
    <main class="app-main">
      <header class="app-head">
        <span class="head-desc">面向污水处理厂进水调度、工艺运行、加药优化、污泥脱水、出水监控与药剂耗材的工艺管理后台。</span>
        <span class="head-user">当前值班：{{ store.operator }} · {{ store.shiftLabel }}</span>
      </header>
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useSessionStore } from '@/stores/session'
import { MODULES } from '@/modules'

const store = useSessionStore()

// 概览固定在第一位，业务模块与路由共用 modules.ts 里的清单
const navItems = [{ label: '运营概览', path: '/' }, ...MODULES]
</script>
