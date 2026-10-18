<template>
  <div class="chart-card card">
    <div v-if="title" class="card-title">{{ title }}</div>
    <div ref="el" class="chart-body"></div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  option: { type: Object, required: true },
  title: { type: String, default: '' },
  height: { type: Number, default: 300 },
})

const el = ref(null)
let chart = null

function render() {
  if (chart) chart.setOption(props.option, true)
}

function resize() {
  if (chart) chart.resize()
}

onMounted(() => {
  chart = echarts.init(el.value)
  render()
  window.addEventListener('resize', resize)
})

watch(
  () => props.option,
  () => render(),
  { deep: true }
)

onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  if (chart) {
    chart.dispose()
    chart = null
  }
})
</script>

<style scoped>
.chart-card {
  height: 100%;
}

.chart-body {
  width: 100%;
  height: v-bind(height + 'px');
  padding: 6px;
}
</style>
