// 院内导航路网数据（来源于 backend/data_source/nav_data，只读副本）
// 每层图：{ floor, width, height, nodes:[{id,x,y,type,name,link?}], edges:[[a,b]] }
import floor1 from './floor1.json'
import floor2 from './floor2.json'
import floor3 from './floor3.json'
import floor4 from './floor4.json'
import verticalLinks from './vertical_links.json'

export const NAV_GRAPHS = {
  1: floor1,
  2: floor2,
  3: floor3,
  4: floor4,
}

export const VERTICAL_LINKS = verticalLinks.links || []

export const FLOORS = [1, 2, 3, 4]

// 节点类型配色（与标注工具/小程序保持一致）
export const NODE_COLOR = {
  junction: '#94a3b8',
  poi: '#2b6de8',
  elev: '#e6a23c',
  stair: '#b8860b',
  escalator: '#9b59b6',
  entrance: '#22c55e',
  hall: '#14b8a6',
  wc: '#7f8c8d',
}
