<template>
  <div class="dashboard">
    <div class="kpi-grid">
      <div v-for="k in kpis" :key="k.label" class="kpi-card">
        <div class="kpi-label">{{ k.label }}</div>
        <div class="kpi-value">{{ k.value }}</div>
        <div class="kpi-sub">{{ k.sub }}</div>
        <div class="kpi-icon" :style="{ background: k.color }">
          <el-icon :size="20"><component :is="k.icon" /></el-icon>
        </div>
      </div>
    </div>

    <div class="chart-grid">
      <ChartCard title="科室分类占比" :option="categoryOption" :height="320" />
      <ChartCard title="楼层科室分布" :option="floorOption" :height="320" />
    </div>
    <div class="chart-grid">
      <ChartCard title="检查须知 · 空腹要求分布" :option="fastingOption" :height="300" />
      <ChartCard title="医生职称分布" :option="doctorOption" :height="300" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useDataStore } from '@/stores/data'
import ChartCard from '@/components/ChartCard.vue'

const data = useDataStore()

const kpis = computed(() => {
  const floors = new Set(data.departments.map((d) => d.floor)).size
  const medCats = new Set(data.medicineGuide.map((m) => m.category)).size
  return [
    { label: '科室总数', value: data.departments.length, sub: `覆盖 ${floors} 个楼层`, icon: 'OfficeBuilding', color: '#0e7490' },
    { label: '医生数', value: data.doctors.length, sub: '在册出诊医生', icon: 'User', color: '#10b981' },
    { label: '检查须知', value: data.examPrep.length, sub: '空腹/非空腹检查条目', icon: 'FirstAidKit', color: '#0ea5e9' },
    { label: '用药常识', value: data.medicineGuide.length, sub: `${medCats} 个用药分类`, icon: 'TakeawayBox', color: '#f59e0b' },
  ]
})

const palette = ['#0e7490', '#0ea5e9', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#ef4444']

const categoryOption = computed(() => {
  const map = {}
  for (const d of data.departments) {
    map[d.category] = (map[d.category] || 0) + 1
  }
  const names = Object.keys(map)
  return {
    color: palette,
    tooltip: { trigger: 'item', formatter: '{b}: {c} 个 ({d}%)' },
    legend: { bottom: 0, icon: 'circle', textStyle: { fontSize: 12 } },
    series: [
      {
        type: 'pie',
        radius: ['42%', '68%'],
        center: ['50%', '44%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
        label: { show: false },
        data: names.map((n) => ({ name: n, value: map[n] })),
      },
    ],
  }
})

const floorOption = computed(() => {
  const floors = [1, 2, 3, 4]
  const counts = floors.map((f) => data.departments.filter((d) => d.floor === f).length)
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 20, top: 30, bottom: 40 },
    xAxis: {
      type: 'category',
      data: floors.map((f) => `${f}F 楼`),
      axisLine: { lineStyle: { color: '#d1d5db' } },
      axisLabel: { color: '#6b7280' },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#eef2f6' } },
    },
    series: [
      {
        type: 'bar',
        data: counts,
        barWidth: 42,
        itemStyle: { borderRadius: [6, 6, 0, 0], color: '#0e7490' },
        label: { show: true, position: 'top', color: '#374151' },
      },
    ],
  }
})

const fastingOption = computed(() => {
  const fasting = data.examPrep.filter((e) => e.fasting === 1).length
  const nonFasting = data.examPrep.length - fasting
  return {
    color: ['#0e7490', '#10b981'],
    tooltip: { trigger: 'item', formatter: '{b}: {c} 项 ({d}%)' },
    legend: { bottom: 0, icon: 'circle', textStyle: { fontSize: 12 } },
    series: [
      {
        type: 'pie',
        radius: '64%',
        center: ['50%', '44%'],
        label: { formatter: '{b}\n{c} 项', fontSize: 12 },
        data: [
          { name: '需空腹', value: fasting },
          { name: '无需空腹', value: nonFasting },
        ],
      },
    ],
  }
})

const doctorOption = computed(() => {
  const map = {}
  for (const doc of data.doctors) {
    map[doc.title] = (map[doc.title] || 0) + 1
  }
  const names = Object.keys(map)
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 20, top: 30, bottom: 40 },
    xAxis: {
      type: 'category',
      data: names,
      axisLabel: { color: '#6b7280' },
      axisLine: { lineStyle: { color: '#d1d5db' } },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#eef2f6' } },
    },
    series: [
      {
        type: 'bar',
        data: names.map((n) => map[n]),
        barWidth: 36,
        itemStyle: { borderRadius: [6, 6, 0, 0], color: '#10b981' },
        label: { show: true, position: 'top', color: '#374151' },
      },
    ],
  }
})
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.chart-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

@media (max-width: 1100px) {
  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .chart-grid {
    grid-template-columns: 1fr;
  }
}
</style>
