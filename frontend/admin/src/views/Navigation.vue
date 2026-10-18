<template>
  <div class="nav-page">
    <div class="page-toolbar">
      <el-radio-group v-model="floor" size="default">
        <el-radio-button v-for="f in floors" :key="f" :value="f">{{ f }}F</el-radio-button>
      </el-radio-group>
      <el-select
        v-model="startId"
        placeholder="选择起点节点"
        style="width: 200px"
        filterable
        @change="computeRoute"
      >
        <el-option v-for="n in startOptions" :key="n.id" :label="n.name" :value="n.id" />
      </el-select>
      <el-select
        v-model="endId"
        placeholder="选择终点（科室/入口）"
        style="width: 220px"
        filterable
        @change="computeRoute"
      >
        <el-option v-for="n in endOptions" :key="n.id" :label="n.name" :value="n.id" />
      </el-select>
      <el-button type="primary" :icon="Aim" @click="computeRoute">规划路线</el-button>
      <el-button :icon="Refresh" @click="clearRoute">清除路线</el-button>
      <div class="spacer"></div>
      <el-button :icon="EditPen" @click="openAnnotator">打开路网标注工具</el-button>
    </div>

    <!-- 路线结果提示 -->
    <el-alert
      v-if="routeInfo"
      :title="routeInfo"
      type="success"
      :closable="false"
      show-icon
      class="route-alert"
    />

    <div class="map-card card">
      <div class="map-wrap">
        <svg :viewBox="`0 0 ${graph.width} ${graph.height}`" class="floor-svg">
          <image :href="`/floors/floor${floor}.jpg`" :x="0" :y="0" :width="graph.width" :height="graph.height" preserveAspectRatio="xMidYMid meet" />
          <!-- 普通边 -->
          <g>
            <line
              v-for="(e, i) in graph.edges"
              :key="'e' + i"
              :x1="nodeMap[e[0]]?.x"
              :y1="nodeMap[e[0]]?.y"
              :x2="nodeMap[e[1]]?.x"
              :y2="nodeMap[e[1]]?.y"
              stroke="#3b82f6"
              stroke-width="2.5"
              stroke-opacity="0.55"
            />
          </g>
          <!-- 规划路线 -->
          <polyline
            v-if="routePoints.length"
            :points="routePoints"
            fill="none"
            stroke="#e91e63"
            stroke-width="6"
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-opacity="0.9"
          />
          <!-- 节点 -->
          <g v-for="n in graph.nodes" :key="n.id">
            <circle
              :cx="n.x"
              :cy="n.y"
              :r="radius(n.type)"
              :fill="colorOf(n.type)"
              stroke="#fff"
              stroke-width="1.5"
            />
          </g>
          <!-- 路线经过节点高亮 -->
          <circle
            v-for="pid in routeNodes"
            :key="'rp' + pid"
            :cx="nodeMap[pid]?.x"
            :cy="nodeMap[pid]?.y"
            r="7"
            fill="none"
            stroke="#e91e63"
            stroke-width="2.5"
          />
          <!-- 起终点 -->
          <g v-if="nodeMap[startId]">
            <circle :cx="nodeMap[startId].x" :cy="nodeMap[startId].y" r="12" fill="#22c55e" stroke="#fff" stroke-width="2" />
            <text :x="nodeMap[startId].x" :y="nodeMap[startId].y - 16" text-anchor="middle" font-size="14" font-weight="700" fill="#16a34a">起</text>
          </g>
          <g v-if="nodeMap[endId]">
            <circle :cx="nodeMap[endId].x" :cy="nodeMap[endId].y" r="12" fill="#e91e63" stroke="#fff" stroke-width="2" />
            <text :x="nodeMap[endId].x" :y="nodeMap[endId].y - 16" text-anchor="middle" font-size="14" font-weight="700" fill="#e91e63">终</text>
          </g>
          <!-- 名称标签 -->
          <g v-for="n in labelNodes" :key="'t' + n.id">
            <text :x="n.x + 9" :y="n.y + 4" font-size="12" fill="#1f2937" style="paint-order: stroke" stroke="#ffffff" stroke-width="3">{{ n.name }}</text>
          </g>
        </svg>
      </div>
    </div>

    <div class="floor-grid">
      <div v-for="f in floorStats" :key="f.floor" class="floor-card card">
        <div class="floor-head">
          <div class="floor-badge">{{ f.floor }}F</div>
          <div class="floor-meta">
            <div class="floor-name">{{ f.name }}</div>
            <div class="floor-hint">{{ f.hint }}</div>
          </div>
        </div>
        <div class="floor-stats">
          <div class="stat">
            <div class="stat-value">{{ f.departments }}</div>
            <div class="stat-label">科室</div>
          </div>
          <div class="stat">
            <div class="stat-value">{{ f.nodes }}</div>
            <div class="stat-label">导航节点</div>
          </div>
          <div class="stat">
            <div class="stat-value">{{ f.edges }}</div>
            <div class="stat-label">路径连线</div>
          </div>
        </div>
      </div>
    </div>

    <ChartCard title="各楼层路网节点分布" :option="nodeOption" :height="300" />

    <div class="hint-box">
      <el-icon><InfoFilled /></el-icon>
      <span>
        平面图与路网为真实数据（与小程序/后端同一套 floorN.json）。选择楼层后指定起点与终点，系统用 Dijkstra 计算最短步行路径并在图上高亮。
        垂直交通（电梯/楼梯）跨楼层关系见 vertical_links，共 {{ verticalCount }} 组。标注工具可导出 JSON 回写后端路网目录。
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Aim, EditPen, InfoFilled, Refresh } from '@element-plus/icons-vue'
import { useDataStore } from '@/stores/data'
import ChartCard from '@/components/ChartCard.vue'
import { NAV_GRAPHS, VERTICAL_LINKS, FLOORS, NODE_COLOR } from '@/data/nav/navGraph'

const data = useDataStore()
const floors = FLOORS

const floorMeta = {
  1: { name: '一楼 · 门急诊与药房', hint: '急诊、儿科、放射、药房' },
  2: { name: '二楼 · 检验与外妇', hint: '检验科、外妇科门诊' },
  3: { name: '三楼 · 专科门诊', hint: '超声、内科、五官科' },
  4: { name: '四楼 · 内镜与体检', hint: '消化内镜、体检、中医' },
}

const floor = ref(1)
const startId = ref('')
const endId = ref('')
const routeNodes = ref([])
const routeLen = ref(0)

const graph = computed(() => NAV_GRAPHS[floor.value])

const nodeMap = computed(() => {
  const m = {}
  for (const n of graph.value.nodes) m[n.id] = n
  return m
})

// 可作为起点：入口 + 大厅
const startOptions = computed(() =>
  graph.value.nodes.filter((n) => ['entrance', 'hall'].includes(n.type))
)
// 可作为终点：所有 poi 科室 + 入口
const endOptions = computed(() =>
  graph.value.nodes.filter((n) => ['poi', 'entrance'].includes(n.type))
)

// 标签只给关键节点，避免拥挤
const labelNodes = computed(() =>
  graph.value.nodes.filter((n) => ['poi', 'entrance', 'hall', 'elev', 'stair', 'escalator'].includes(n.type))
)

function colorOf(type) {
  return NODE_COLOR[type] || '#94a3b8'
}
function radius(type) {
  if (type === 'poi') return 6
  if (['entrance', 'hall'].includes(type)) return 7
  return 4
}

// 楼层切换时重置选中与路线
floor.value = 1
startId.value = graph.value.nodes.find((n) => n.type === 'entrance')?.id || ''

// 监听楼层变化重置
watch(floor, (f) => {
  const g = NAV_GRAPHS[f]
  startId.value = g.nodes.find((n) => n.type === 'entrance')?.id || ''
  endId.value = ''
  routeNodes.value = []
  routeLen.value = 0
})

// 建邻接表并跑 Dijkstra（欧氏距离加权）
function dijkstra(start, end) {
  const g = graph.value
  const adj = {}
  const ensure = (id) => {
    if (!adj[id]) adj[id] = []
  }
  for (const [a, b] of g.edges) {
    ensure(a); ensure(b)
    const na = nodeMap.value[a]
    const nb = nodeMap.value[b]
    const w = Math.hypot(na.x - nb.x, na.y - nb.y)
    adj[a].push({ to: b, w })
    adj[b].push({ to: a, w })
  }
  const dist = { [start]: 0 }
  const prev = {}
  const visited = new Set()
  while (true) {
    let u = null
    let best = Infinity
    for (const id in dist) {
      if (!visited.has(id) && dist[id] < best) {
        best = dist[id]
        u = id
      }
    }
    if (u === null) break
    if (u === end) break
    visited.add(u)
    for (const edge of adj[u] || []) {
      const nd = dist[u] + edge.w
      if (dist[edge.to] === undefined || nd < dist[edge.to]) {
        dist[edge.to] = nd
        prev[edge.to] = u
      }
    }
  }
  if (dist[end] === undefined) return null
  const path = []
  let cur = end
  while (cur) {
    path.unshift(cur)
    cur = prev[cur]
  }
  return { path, len: dist[end] }
}

function computeRoute() {
  if (!startId.value || !endId.value) {
    ElMessage.warning('请先选择起点和终点')
    return
  }
  if (startId.value === endId.value) {
    ElMessage.warning('起点与终点相同')
    return
  }
  const res = dijkstra(startId.value, endId.value)
  if (!res) {
    ElMessage.error('未找到连通路径')
    routeNodes.value = []
    routeLen.value = 0
    return
  }
  routeNodes.value = res.path
  routeLen.value = res.len
}

const routePoints = computed(() =>
  routeNodes.value.map((id) => `${nodeMap.value[id]?.x},${nodeMap.value[id]?.y}`).join(' ')
)

const routeInfo = computed(() => {
  if (!routeNodes.value.length) return ''
  const s = nodeMap.value[routeNodes.value[0]]
  const e = nodeMap.value[routeNodes.value[routeNodes.value.length - 1]]
  return `已找到 ${floor.value}F 内最短路径：${s?.name} → ${e?.name}，共 ${routeNodes.value.length} 个节点，步行约 ${(routeLen.value / 60).toFixed(1)} 分钟（按 60 像素≈1 米折算，仅演示）`
})

function clearRoute() {
  routeNodes.value = []
  routeLen.value = 0
}

const floorStats = computed(() =>
  floors.map((f) => {
    const g = NAV_GRAPHS[f]
    return {
      floor: f,
      ...floorMeta[f],
      departments: data.departments.filter((d) => d.floor === f).length,
      nodes: g.nodes.length,
      edges: g.edges.length,
    }
  })
)

const verticalCount = VERTICAL_LINKS.length

const nodeOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 40, right: 20, top: 30, bottom: 40 },
  xAxis: {
    type: 'category',
    data: floorStats.value.map((f) => `${f.floor}F`),
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
      name: '导航节点',
      type: 'bar',
      data: floorStats.value.map((f) => f.nodes),
      barWidth: 42,
      itemStyle: { borderRadius: [6, 6, 0, 0], color: '#0ea5e9' },
      label: { show: true, position: 'top', color: '#374151' },
    },
  ],
}))

function openAnnotator() {
  window.open(import.meta.env.BASE_URL + 'map-annotator.html', '_blank')
}
</script>

<style scoped>
.nav-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.route-alert {
  margin-bottom: 0;
}

.map-card {
  padding: 12px;
}

.map-wrap {
  width: 100%;
  background: #e8ecf1;
  border-radius: 8px;
  overflow: hidden;
}

.floor-svg {
  display: block;
  width: 100%;
  height: auto;
}

.floor-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.floor-card {
  padding: 18px;
}

.floor-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.floor-badge {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, #0e7490, #0ea5e9);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
  flex-shrink: 0;
}

.floor-name {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}

.floor-hint {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 3px;
}

.floor-stats {
  display: flex;
  gap: 10px;
}

.stat {
  flex: 1;
  text-align: center;
  background: #f8fafc;
  border-radius: 8px;
  padding: 10px 0;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: #0e7490;
}

.stat-label {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 4px;
}

.hint-box {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px 16px;
  border-radius: 10px;
  background: #eef6ff;
  border: 1px solid #dbeafe;
  color: #374151;
  font-size: 13px;
  line-height: 1.8;
}

.hint-box .el-icon {
  color: #0e7490;
  margin-top: 3px;
}

@media (max-width: 1100px) {
  .floor-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
