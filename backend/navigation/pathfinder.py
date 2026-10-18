# -*- coding: utf-8 -*-
"""Dijkstra 最短路寻路(移植自 simpleroutingsvg 的 shortestway 库)。

输出: 分楼层的路径段(像素坐标序列) + 面向老人的分步指引文字。
"""
import heapq
import os
import sys
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from graph import NavGraph, PX_PER_METER, Node

# 垂直交通的动作文案
VERT_ACTION = {"elev": "乘电梯", "stair": "走楼梯", "escalator": "乘扶梯"}
VERT_TYPE = {"elev", "stair", "escalator"}


def dijkstra(graph: NavGraph, start_id: str, end_id: str) -> Optional[list]:
    """返回 start->end 的最短节点序列, 不可达返回 None。"""
    if start_id not in graph.nodes or end_id not in graph.nodes:
        return None
    dist = {start_id: 0.0}
    prev: dict = {}
    pq = [(0.0, start_id)]
    visited = set()
    while pq:
        d, cur = heapq.heappop(pq)
        if cur in visited:
            continue
        visited.add(cur)
        if cur == end_id:
            break
        for nxt, w in graph.neighbors(cur):
            nd = d + w
            if nd < dist.get(nxt, float("inf")):
                dist[nxt] = nd
                prev[nxt] = cur
                heapq.heappush(pq, (nd, nxt))
    if end_id not in dist:
        return None
    path = [end_id]
    while path[-1] != start_id:
        path.append(prev[path[-1]])
    path.reverse()
    return path


def find_route(graph: NavGraph, start_id: str, end_id: str) -> Optional[dict]:
    """寻路并生成面向用户的路线说明。"""
    path = dijkstra(graph, start_id, end_id)
    if path is None:
        return None
    nodes = [graph.nodes[nid] for nid in path]

    # 按楼层切分成路径段
    segments = []
    current = {"floor": nodes[0].floor, "points": [], "node_ids": []}
    for i, node in enumerate(nodes):
        if node.floor != current["floor"]:
            segments.append(current)
            current = {"floor": node.floor, "points": [], "node_ids": []}
        current["points"].append([node.x, node.y])
        current["node_ids"].append(node.id)
    segments.append(current)
    # 标记"纯途经层": 该楼层段只有垂直交通落点、没有实际行走,
    # 前端跳层时应跳过它, 直接到真正需要行走的楼层。
    for _seg in segments:
        _seg["pass"] = len(_seg["points"]) < 2

    steps = _build_steps(nodes)
    total_px = 0.0
    for i in range(1, len(path)):
        total_px += _edge_weight(graph, path[i - 1], path[i])
    return {
        "start": _node_brief(nodes[0]),
        "end": _node_brief(nodes[-1]),
        "distance_px": round(total_px, 1),
        "distance_m": round(total_px / PX_PER_METER, 1),
        "segments": segments,
        "steps": steps,
    }


def _edge_weight(graph: NavGraph, a: str, b: str) -> float:
    for nxt, w in graph.neighbors(a):
        if nxt == b:
            return w
    return 0.0


def _node_brief(node: Node) -> dict:
    return {"id": node.id, "name": node.name, "floor": node.floor, "type": node.type, "x": node.x, "y": node.y}


def _build_steps(nodes: list) -> list:
    """把节点序列翻译成大白话步骤。

    连续的同种垂直换层(如手扶梯 1F->2F->3F)会合并成一条"乘扶梯到3楼"的指引,
    并提醒用户中间楼层不用下、注意核对是否到了目标楼层。
    垂直行程在"开始步行/换成其他换层方式/路线结束"时落盘, 保证顺序正确。
    """
    steps = []
    walk_start = nodes[0]
    walk_dist = 0.0
    # 正在累计的垂直行程: {kind, start_name, start_floor, end_floor, end_name, pass_floors}
    vert = None

    def flush_walk():
        nonlocal walk_dist
        if walk_dist > 5:
            meters = round(walk_dist / PX_PER_METER)
            steps.append({
                "kind": "walk", "floor": walk_start.floor,
                "text": f"从{walk_start.name}步行约{meters}米",
            })

    def flush_vert():
        nonlocal vert
        if vert:
            action = VERT_ACTION.get(vert["kind"], "换层")
            text = f"在{vert['start_name']}{action}到{vert['end_floor']}楼"
            notice = ""
            if abs(vert["end_floor"] - vert["start_floor"]) > 1 and vert["pass_floors"]:
                mid = "、".join(str(f) for f in vert["pass_floors"])
                notice = f"中间{mid}楼不用下, 到{vert['end_floor']}楼前注意看楼层标识, 确认是不是目标楼层"
            steps.append({
                "kind": vert["kind"], "floor": vert["end_floor"],
                "text": text, "notice": notice,
            })
            vert = None

    for i in range(1, len(nodes)):
        prev, cur = nodes[i - 1], nodes[i]
        if prev.floor != cur.floor:
            # 垂直换层
            if vert is None:
                flush_walk()  # 换层前的步行先落盘
                vert = {
                    "kind": prev.type, "start_name": prev.name,
                    "start_floor": prev.floor, "end_floor": cur.floor,
                    "end_name": cur.name, "pass_floors": [],
                }
            elif vert["kind"] == prev.type:
                # 同种垂直交通继续向上/向下延伸, 上一站记为"不用下的楼层"
                vert["pass_floors"].append(vert["end_floor"])
                vert["end_floor"] = cur.floor
                vert["end_name"] = cur.name
            else:
                flush_vert()
                flush_walk()
                vert = {
                    "kind": prev.type, "start_name": prev.name,
                    "start_floor": prev.floor, "end_floor": cur.floor,
                    "end_name": cur.name, "pass_floors": [],
                }
            walk_start = cur
            walk_dist = 0.0
        else:
            # 同层步行: 若刚从垂直行程落地, 先落盘该行程
            if vert is not None:
                flush_vert()
            seg_len = ((prev.x - cur.x) ** 2 + (prev.y - cur.y) ** 2) ** 0.5
            walk_dist += seg_len
    flush_vert()
    flush_walk()
    steps.append({"kind": "arrive", "floor": nodes[-1].floor, "text": f"到达{nodes[-1].name}"})
    return steps
