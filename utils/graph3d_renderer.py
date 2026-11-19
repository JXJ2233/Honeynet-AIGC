from __future__ import annotations

"""
MoE-SHD 3D 全息攻防沙盘渲染引擎 · Pro 版
"""

from dataclasses import dataclass
import hashlib
import json
import math
import random
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import networkx as nx


@dataclass
class TopologyPayload:
    stage1_nodes: List[Dict[str, Any]]
    stage1_edges: List[Dict[str, Any]]
    stage2_nodes: List[Dict[str, Any]]
    stage2_edges: List[Dict[str, Any]]
    stage3_nodes: List[Dict[str, Any]]
    stage3_edges: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class Graph3DRenderer:
    def __init__(
        self,
        backend_url: str = "http://127.0.0.1:8000",
        seed: int = 42,
        node_count: int = 232,
        prefer_backend: bool = True,
    ):
        self.backend_url = backend_url.rstrip("/")
        self.seed = seed
        self.node_count = node_count
        self.prefer_backend = prefer_backend
        self.scene: str = "通用数据中心"
        self._payload_cache: Optional[TopologyPayload] = None

        self.colors = {
            "bg": "#030407",
            "text": "#E2E8F0",
            "internet": "#38BDF8",
            "core": "#3B82F6",
            "scb": "#8B5CF6",
            "aggregation": "#10B981",
            "edge": "#64748B",
            "server": "#F59E0B",
            "honeypot": "#EC4899",
            "honeypot_active": "#EF4444",
            "edge_normal": "rgba(100, 116, 139, 0.15)",
            "edge_steiner": "rgba(56, 189, 248, 0.8)",
            "particle": "#EF4444",
        }

    def _generate_ip(self, nid: str, layer: str) -> str:
        """根据节点ID的哈希生成稳定的仿真IP地址"""
        subnet = {
            "internet": "8.8.", "core": "10.0.", "scb": "10.1.",
            "aggregation": "172.16.", "edge": "192.168.",
            "server": "172.20.", "honeypot": "10.99."
        }.get(layer, "10.10.")
        h = int(hashlib.md5(nid.encode()).hexdigest(), 16)
        return f"{subnet}{(h // 256) % 255}.{h % 254 + 1}"

    def build_payload(self) -> TopologyPayload:
        if self._payload_cache is not None:
            return self._payload_cache

        payload = None
        if self.prefer_backend:
            raw = self.fetch_backend_payload()
            if raw:
                candidate = self._normalize_backend_payload(raw)
                if self._looks_like_large_topology(candidate):
                    payload = candidate

        if payload is None:
            payload = self._generate_mock_payload(node_count=self.node_count, seed=self.seed)

        self._payload_cache = payload
        return payload

    def refresh(self) -> TopologyPayload:
        self._payload_cache = None
        return self.build_payload()

    def fetch_backend_payload(self, timeout: float = 4.0) -> Optional[Dict[str, Any]]:
        try:
            import requests
            resp = requests.get(
                f"{self.backend_url}/api/topology/steiner-steps",
                params={"node_count": self.node_count, "seed": self.seed, "attack_scene": "general"},
                timeout=timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

    def _looks_like_large_topology(self, payload: TopologyPayload) -> bool:
        return len(payload.stage1_nodes) >= 50

    def _normalize_backend_payload(self, raw: Dict[str, Any]) -> TopologyPayload:
        data = raw.get("data", raw)
        stage1 = data.get("stage1_base_network", {}) or {}
        nodes1 = self._normalize_nodes(stage1.get("nodes", []))
        edges1 = self._normalize_edges(stage1.get("edges", []))

        stage2 = data.get("stage2_scb_filter") or data.get("stage2_scb_filtered") or {}
        stage3 = data.get("stage4_steiner_tree") or data.get("stage3_steiner_tree") or {}

        nodes2 = self._normalize_stage2_nodes(stage2, nodes1, edges1)
        edges2 = self._normalize_stage2_edges(stage2, nodes1, edges1, nodes2)
        nodes3 = self._normalize_stage3_nodes(stage3, nodes1, edges1, nodes2)
        edges3 = self._normalize_stage3_edges(stage3, nodes1, edges1, nodes3)

        return TopologyPayload(
            stage1_nodes=nodes1, stage1_edges=edges1,
            stage2_nodes=nodes2, stage2_edges=edges2,
            stage3_nodes=nodes3, stage3_edges=edges3,
            metadata={"source": "backend"}
        )

    def _normalize_nodes(self, nodes: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out = []
        for idx, node in enumerate(nodes):
            nid = str(node.get("id", node.get("node_id", idx)))
            layer = node.get("layer", "access")
            out.append({
                "id": nid, "name": node.get("name", nid), "layer": layer,
                "ip": node.get("ip") or self._generate_ip(nid, layer),
                "honeypot_capability": bool(node.get("honeypot_capability", False)),
                "visible": bool(node.get("visible", True)), "active": bool(node.get("active", False)),
                "x": node.get("x"), "y": node.get("y"), "z": node.get("z"),
            })
        return out

    def _normalize_edges(self, edges: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out = []
        for edge in edges:
            if not isinstance(edge, dict): continue
            u, v = edge.get("u", edge.get("source")), edge.get("v", edge.get("target"))
            if u is None or v is None: continue
            out.append({
                "u": str(u), "v": str(v), "weight": float(edge.get("weight", 1.0)),
                "visible": True, "is_steiner": bool(edge.get("is_steiner", False)),
            })
        return out

    def _normalize_stage2_nodes(self, stage2, nodes1, edges1):
        G = self._build_nx_graph(nodes1, edges1)
        degree_centrality = nx.degree_centrality(G) if G.number_of_nodes() else {}
        scored = []
        for node in nodes1:
            score = {"internet": 12, "core": 11, "scb": 10, "aggregation": 8, "server": 6, "honeypot": 9.5}.get(node.get("layer", "access"), 2.0)
            score += degree_centrality.get(node["id"], 0.0) * 7.0
            scored.append((score, node))
        scored.sort(key=lambda x: x[0], reverse=True)
        keep_n = max(108, min(132, int(len(nodes1) * 0.52)))
        kept = {node["id"] for _, node in scored[:keep_n]}
        return [dict(node, visible=node["id"] in kept) for node in nodes1]

    def _normalize_stage2_edges(self, stage2, nodes1, edges1, nodes2):
        visible_nodes = {n["id"] for n in nodes2 if n.get("visible", True)}
        return [dict(edge, visible=edge["u"] in visible_nodes and edge["v"] in visible_nodes) for edge in edges1]

    def _normalize_stage3_nodes(self, stage3, nodes1, edges1, nodes2):
        selected = {n["id"] for n in nodes1 if n.get("layer") in ("internet", "core", "scb")}
        for n in nodes1:
            if n.get("layer") == "honeypot":
                selected.add(n["id"])
        out = []
        for node in nodes1:
            visible = node["id"] in selected
            out.append(dict(
                node, visible=visible,
                active=visible and node.get("honeypot_capability", False) and node.get("layer") in ("aggregation", "honeypot")
            ))
        return out

    def _normalize_stage3_edges(self, stage3, nodes1, edges1, nodes3):
        return self._derive_steiner_edges(nodes1, edges1, nodes3)

    def _generate_mock_payload(self, node_count: int = 232, seed: int = 42) -> TopologyPayload:
        rng = random.Random(seed)

        # ========== 1. 根据场景定义节点数量分布（行业特征） ==========
        if self.scene == "金融结算中心":
            counts = {
                "internet": 4, "core": 32, "scb": 40,
                "aggregation": 60, "edge": 90, "server": 140, "honeypot": 50
            }
            # 金融：核心层极密，服务器数量多，防御纵深大
        elif self.scene == "政务数据专网":
            counts = {
                "internet": 3, "core": 28, "scb": 36,
                "aggregation": 48, "edge": 72, "server": 110, "honeypot": 45
            }
            # 政务：安全要求高，蜜罐多，核心层密集
        elif self.scene == "工业控制系统":
            counts = {
                "internet": 2, "core": 8, "scb": 18,
                "aggregation": 45, "edge": 70, "server": 45, "honeypot": 30
            }
            # 工业：SCADA/PLC 集中在汇聚层，边缘中等，总节点约 218
        elif self.scene == "医疗物联网":
            counts = {
                "internet": 2, "core": 6, "scb": 14,
                "aggregation": 35, "edge": 120, "server": 30, "honeypot": 20
            }
            # 医疗：边缘设备极多，核心极简
        elif self.scene == "边缘算力网络":
            counts = {
                "internet": 2, "core": 6, "scb": 10,
                "aggregation": 30, "edge": 100, "server": 20, "honeypot": 25
            }
            # 边缘：边缘层主导，资源受限，总节点约 193
        else:  # 通用数据中心（fallback）
            counts = {
                "internet": 2, "core": 12, "scb": 22,
                "aggregation": 36, "edge": 80, "server": 56, "honeypot": 24
            }

        # ========== 2. 根据场景定义每层半径范围（决定球体视觉大小） ==========
        if self.scene == "金融结算中心":
            layout_radii = {
                "core": 40.0, "scb": 70.0, "aggregation": 110.0,
                "server": 150.0, "edge": 190.0, "honeypot": 230.0, "internet": 270.0
            }
        elif self.scene == "政务数据专网":
            layout_radii = {
                "core": 45.0, "scb": 75.0, "aggregation": 115.0,
                "server": 155.0, "edge": 195.0, "honeypot": 235.0, "internet": 275.0
            }
        elif self.scene == "工业控制系统":
            layout_radii = {
                "core": 35.0, "scb": 65.0, "aggregation": 100.0,
                "server": 135.0, "edge": 175.0, "honeypot": 215.0, "internet": 255.0
            }
        elif self.scene == "医疗物联网":
            layout_radii = {
                "core": 30.0, "scb": 55.0, "aggregation": 85.0,
                "server": 120.0, "edge": 160.0, "honeypot": 200.0, "internet": 240.0
            }
        elif self.scene == "边缘算力网络":
            layout_radii = {
                "core": 25.0, "scb": 50.0, "aggregation": 80.0,
                "server": 110.0, "edge": 150.0, "honeypot": 190.0, "internet": 230.0
            }
        else:  # 通用数据中心
            layout_radii = {
                "core": 30.0, "scb": 60.0, "aggregation": 100.0,
                "server": 140.0, "edge": 180.0, "honeypot": 220.0, "internet": 260.0
            }

        # ========== 3. 生成节点（球形均匀分布，但半径按层不同 = 同心球壳） ==========
        nodes: List[Dict[str, Any]] = []
        layer_ids: Dict[str, List[str]] = {}
        golden_ratio = (1 + 5 ** 0.5) / 2

        for layer, radius in layout_radii.items():
            n = counts.get(layer, 0)
            if n == 0: continue
            ids = [f"{layer}_{i:02d}" for i in range(n)]
            layer_ids[layer] = ids
            for idx, nid in enumerate(ids):
                # Fibonacci 球体均匀分布，但半径使用该层的半径（形成多层球壳）
                theta = 2 * math.pi * idx / golden_ratio
                phi = math.acos(1 - 2 * (idx + 0.5) / n)
                r = radius + rng.uniform(-radius * 0.05, radius * 0.05)  # 微小扰动，避免完美对称
                x = r * math.sin(phi) * math.cos(theta)
                y = r * math.sin(phi) * math.sin(theta)
                z = r * math.cos(phi)
                nodes.append({
                    "id": nid, "name": nid.upper(), "layer": layer,
                    "ip": self._generate_ip(nid, layer),
                    "honeypot_capability": layer == "honeypot",
                    "visible": True, "active": False,
                    "x": round(x, 2), "y": round(y, 2), "z": round(z, 2),
                })

        # ========== 4. 生成边（连接规则按层，最终边密度随场景变化） ==========
        edges: List[Dict[str, Any]] = []
        edge_keys = set()

        def add_edge(u: str, v: str, w: float = 1.0):
            if u == v: return
            key = tuple(sorted((u, v)))
            if key in edge_keys: return
            edge_keys.add(key)
            edges.append({"u": u, "v": v, "weight": round(w, 2), "visible": True, "is_steiner": False})

        # ---- 骨干连接：Internet -> Core ----
        for u in layer_ids.get("internet", []):
            for v in layer_ids.get("core", []):
                add_edge(u, v, rng.uniform(0.75, 1.0))

        # ---- Core 内部全互联 ----
        core_ids = layer_ids.get("core", [])
        for i in range(len(core_ids)):
            for j in range(i + 1, len(core_ids)):
                add_edge(core_ids[i], core_ids[j], rng.uniform(0.85, 1.0))

        # ---- SCB 连接到 Core 和 Aggregation ----
        for u in layer_ids.get("scb", []):
            for v in self._pick_k(layer_ids.get("core", []), k=4, rng=rng):
                add_edge(u, v, rng.uniform(0.7, 0.95))
            for v in self._pick_k(layer_ids.get("aggregation", []), k=4, rng=rng):
                add_edge(u, v, rng.uniform(0.55, 0.85))

        # ---- Aggregation 连接到 Edge 和 Server ----
        for u in layer_ids.get("aggregation", []):
            for v in self._pick_k(layer_ids.get("edge", []), k=5, rng=rng):
                add_edge(u, v, rng.uniform(0.42, 0.76))
            for v in self._pick_k(layer_ids.get("server", []), k=3, rng=rng):
                add_edge(u, v, rng.uniform(0.36, 0.68))

        # ---- Server 连接到 Edge 和 Honeypot ----
        for u in layer_ids.get("server", []):
            for v in self._pick_k(layer_ids.get("edge", []), k=4, rng=rng):
                add_edge(u, v, rng.uniform(0.30, 0.60))
            for v in self._pick_k(layer_ids.get("honeypot", []), k=3, rng=rng):
                add_edge(u, v, rng.uniform(0.35, 0.65))

        # ---- Honeypot 连接到 SCB ----
        for u in layer_ids.get("honeypot", []):
            for v in self._pick_k(layer_ids.get("scb", []), k=3, rng=rng):
                add_edge(u, v, rng.uniform(0.42, 0.82))

        # ========== 5. 额外随机边（密度随场景调整） ==========
        all_ids = [n["id"] for n in nodes]
        # 根据场景调整总边数倍数
        if self.scene == "金融结算中心":
            edge_multiplier = 5.5
        elif self.scene == "政务数据专网":
            edge_multiplier = 5.0
        elif self.scene == "医疗物联网":
            edge_multiplier = 4.0
        elif self.scene == "工业控制系统":
            edge_multiplier = 4.5
        elif self.scene == "教育科研云":
            edge_multiplier = 4.0
        elif self.scene == "边缘算力网络":
            edge_multiplier = 3.5
        else:
            edge_multiplier = 4.0
        target_edges = int(len(nodes) * edge_multiplier)
        attempts = 0
        while len(edges) < target_edges and attempts < target_edges * 20:
            attempts += 1
            u = rng.choice(all_ids)
            # 随机选择另一层的节点，增加跨层连接
            target_layers = list(layout_radii.keys())
            target_layer = rng.choice(target_layers)
            if target_layer not in layer_ids: continue
            v = rng.choice(layer_ids[target_layer])
            if v == u: continue
            add_edge(u, v, rng.uniform(0.15, 0.92))

        # ========== 6. 后续的 stage2/stage3 筛选逻辑与原代码一致 ==========
        G = self._build_nx_graph(nodes, edges)
        degree_centrality = nx.degree_centrality(G) if G.number_of_nodes() else {}

        scored = []
        for node in nodes:
            score = {"internet": 10, "core": 12, "scb": 11, "aggregation": 8.5, "edge": 4, "server": 5, "honeypot": 9.5}.get(node["layer"], 1)
            if node["honeypot_capability"]: score += 3
            score += degree_centrality.get(node["id"], 0.0) * 7.0 + rng.random()
            scored.append((score, node))
        scored.sort(key=lambda x: x[0], reverse=True)

        keep_stage2 = {node["id"] for _, node in scored[:int(len(nodes) * 0.55)]}
        stage2_nodes = [dict(node, visible=node["id"] in keep_stage2) for node in nodes]
        stage2_edges = [dict(edge, visible=edge["u"] in keep_stage2 and edge["v"] in keep_stage2) for edge in edges]

        selected = {n["id"] for n in nodes if n["layer"] in ("internet", "core", "scb")}
        honeypots = [n for n in nodes if n["layer"] == "honeypot"]
        honeypots.sort(key=lambda n: degree_centrality.get(n["id"], 0.0), reverse=True)
        for n in honeypots[: max(5, int(len(honeypots) * 0.5))]:
            selected.add(n["id"])

        stage3_nodes = [dict(node, visible=node["id"] in selected, active=(node["id"] in selected and node["layer"] == "honeypot")) for node in nodes]
        stage3_edges = self._derive_steiner_edges(nodes, edges, stage3_nodes)

        return TopologyPayload(
            stage1_nodes=nodes, stage1_edges=edges,
            stage2_nodes=stage2_nodes, stage2_edges=stage2_edges,
            stage3_nodes=stage3_nodes, stage3_edges=stage3_edges,
            metadata={"source": "mock", "scene": self.scene},
        )

    def _pick_k(self, items: List[str], k: int, rng: random.Random) -> List[str]:
        if not items: return []
        if k >= len(items): return list(items)
        return rng.sample(items, k)

    def _derive_steiner_edges(self, nodes, edges, stage3_nodes):
        G = self._build_nx_graph(nodes, edges)
        visible = [n["id"] for n in stage3_nodes if n.get("visible")]
        visible_set = set(visible)
        if not visible: return []
        root = next((n["id"] for n in stage3_nodes if n.get("layer") in ("internet", "core") and n.get("visible")), visible[0])
        pairs = []
        for target in visible:
            if target == root: continue
            try:
                path = nx.shortest_path(G, root, target)
                for a, b in zip(path[:-1], path[1:]):
                    if a in visible_set and b in visible_set:
                        pairs.append((a, b))
            except Exception:
                continue

        uniq = []
        seen = set()
        for a, b in pairs:
            key = tuple(sorted((a, b)))
            if key in seen: continue
            seen.add(key)
            uniq.append({"u": a, "v": b, "weight": 1.0, "visible": True, "is_steiner": True})
        return uniq

    def _build_nx_graph(self, nodes, edges):
        G = nx.Graph()
        for n in nodes: G.add_node(n["id"])
        for e in edges: G.add_edge(str(e["u"]), str(e["v"]))
        return G

    def node_position(self, node: Dict[str, Any], index: int, total: int) -> Tuple[float, float, float]:
        if all(node.get(k) is not None for k in ("x", "y", "z")):
            return float(node["x"]), float(node["y"]), float(node["z"])
        return 0.0, 0.0, 0.0

    def node_visual(self, node: Dict[str, Any], stage: int) -> Tuple[str, float, float]:
        layer = node.get("layer", "edge")
        honeypot = bool(node.get("honeypot_capability", False))
        active = bool(node.get("active", False))

        if layer == "internet": return self.colors["internet"], 20, 1.0
        if layer == "core": return self.colors["core"], 20, 1.0
        if layer == "scb": return self.colors["scb"], 14, 0.98
        if layer == "aggregation":
            if stage == 2 and active: return self.colors["honeypot_active"], 16, 1.0
            if honeypot: return self.colors["honeypot"], 14, 0.96
            return self.colors["aggregation"], 12, 0.92
        if layer == "server": return self.colors["server"], 10, 0.88
        if layer == "honeypot": return self.colors["honeypot_active"] if active else self.colors["honeypot"], 14, 1.0

        if stage == 1: return self.colors["edge"], 7, 0.08
        return self.colors["edge"], 6, 0.48

    def get_stage(self, stage: int) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        payload = self.build_payload()
        if stage == 0: return payload.stage1_nodes, payload.stage1_edges
        if stage == 1: return payload.stage2_nodes, payload.stage2_edges
        return payload.stage3_nodes, payload.stage3_edges

    def get_stage_stats(self, stage: int) -> Dict[str, Any]:
        payload = self.build_payload()
        nodes, edges = self.get_stage(stage)
        visible_nodes = [n for n in nodes if n.get("visible", True)]
        total = len(payload.stage1_nodes)
        node_count = len(visible_nodes)
        edge_count = len([e for e in edges if e.get("visible", True)])
        saving = 0.0 if stage == 0 else round(max(0.0, (total - node_count) / max(total, 1) * 100), 1)

        if stage == 0: status = "State: Vulnerable & Exposed"
        elif stage == 1: status = "State: Filtering Redundancy"
        else: status = f"State: Secured, Compute Saving {saving}%"

        return {"node_count": node_count, "edge_count": edge_count, "saving": saving, "status": status}

    def get_attack_target(self) -> Optional[str]:
        nodes, _ = self.get_stage(2)
        candidates = [n for n in nodes if n.get("visible", False) and n.get("honeypot_capability", False)]
        if not candidates: candidates = [n for n in nodes if n.get("visible", False)]
        if not candidates: return None
        active = [n for n in candidates if n.get("active")]
        pool = active or candidates
        pool.sort(key=lambda n: n["id"])
        return pool[0]["id"]

    def build_attack_path(self, target_id: Optional[str] = None) -> List[str]:
        payload = self.build_payload()
        nodes3, edges3 = payload.stage3_nodes, payload.stage3_edges
        if not target_id: target_id = self.get_attack_target()
        if not target_id: return []

        visible_nodes = [n for n in nodes3 if n.get("visible", False)]
        root = next((n["id"] for n in visible_nodes if n.get("layer") in ("internet", "core")), None)
        if not root and visible_nodes: root = visible_nodes[0]["id"]
        if not root: return []

        G = nx.Graph()
        for n in visible_nodes: G.add_node(n["id"])
        for e in edges3:
            if e.get("visible", True): G.add_edge(str(e["u"]), str(e["v"]))
        try:
            return [str(x) for x in nx.shortest_path(G, root, target_id)]
        except Exception:
            return [root, target_id]

    def render_stage_html(
        self,
        stage: int,
        attack_path: Optional[List[str]] = None,
        height: int = 760,
    ) -> str:
        nodes, edges = self.get_stage(stage)
        visible_nodes = [n for n in nodes if n.get("visible", True)]

        positions = {}
        for idx, node in enumerate(visible_nodes):
            pos = self.node_position(node, idx, len(visible_nodes))
            positions[node["id"]] = (float(pos[0]), float(pos[1]), float(pos[2]))

        nodes_data = []
        for node in visible_nodes:
            if node["id"] not in positions: continue
            x, y, z = positions[node["id"]]
            color, size, opacity = self.node_visual(node, stage)

            nodes_data.append({
                "id": node["id"],
                "name": node["name"],
                "layer": node["layer"],
                "ip": node.get("ip", "Unknown"),
                "status": "Honeypot (Active)" if node.get("active") else "Secured Node",
                "value": [x, y, z],
                "symbolSize": size,
                "itemStyle": {"color": color, "opacity": opacity}
            })

        normal_line_data = []
        steiner_line_data = []
        for e in edges:
            if not e.get("visible", True): continue
            u, v = str(e["u"]), str(e["v"])
            if u not in positions or v not in positions: continue

            line = [list(positions[u]), list(positions[v])]
            if stage == 2 and e.get("is_steiner", False):
                steiner_line_data.append(line)
            else:
                normal_line_data.append(line)

        return self._wrap_html(nodes_data, normal_line_data, steiner_line_data, attack_path, height=height)

    def _wrap_html(self, nodes_data: List[Any], normal_lines: List[Any], steiner_lines: List[Any], attack_path: Optional[List[str]], height: int) -> str:
        nodes_json = json.dumps(nodes_data, ensure_ascii=False)
        normal_json = json.dumps(normal_lines)
        steiner_json = json.dumps(steiner_lines)
        attack_path_json = json.dumps(attack_path or [])

        return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <style>
    html, body {{ margin: 0; padding: 0; background: #030407; overflow: hidden; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
    #three-container {{ width: 100%; height: {height}px; }}

    /* 高级感悬浮信息框 */
    #tooltip {{
        position: absolute; display: none;
        background: rgba(11, 14, 20, 0.85);
        backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
        border: 1px solid #1C212B; color: #E2E8F0;
        padding: 16px; border-radius: 8px; font-size: 13px;
        pointer-events: none; z-index: 100;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        min-width: 200px;
    }}
    .tt-header {{ font-weight: 600; color: #FFFFFF; margin-bottom: 10px; font-size: 14px; border-bottom: 1px solid #1C212B; padding-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }}
    .tt-row {{ display: flex; justify-content: space-between; margin-bottom: 6px; }}
    .tt-label {{ color: #8B949E; }}
    .tt-value {{ color: #E2E8F0; font-family: 'SF Mono', Consolas, monospace; }}

    /* 攻击拦截警报 */
    #attack-alert {{
        position: absolute; top: 30px; left: 50%; transform: translateX(-50%);
        display: none; background: rgba(239, 68, 68, 0.15);
        border: 1px solid #EF4444; color: #EF4444;
        padding: 12px 24px; border-radius: 6px; font-size: 14px; font-weight: 600;
        z-index: 100; text-transform: uppercase; letter-spacing: 1px;
        backdrop-filter: blur(4px); box-shadow: 0 0 20px rgba(239, 68, 68, 0.2);
        animation: pulse-border 1.5s infinite;
    }}
    @keyframes pulse-border {{
        0% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }}
        70% {{ box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }}
    }}
  </style>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>
  <div id="three-container"></div>
  <div id="tooltip"></div>
  <div id="attack-alert">Threat Isolated : Honeypot Engaged</div>
  <script>
    (function() {{
      var nodesData = {nodes_json};
      var normalLines = {normal_json};
      var steinerLines = {steiner_json};
      var attackPath = {attack_path_json};

      var container = document.getElementById('three-container');
      var tooltip = document.getElementById('tooltip');

      function initThree() {{
          if (container.clientWidth === 0) {{ setTimeout(initThree, 100); return; }}

          var width = container.clientWidth;
          var height = container.clientHeight;

          var scene = new THREE.Scene();
          scene.background = new THREE.Color(0x030407);

          var camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 3000);
          camera.position.set(380, 220, 380);

          var renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
          renderer.setSize(width, height);
          renderer.setPixelRatio(window.devicePixelRatio);
          container.appendChild(renderer.domElement);

          var controls = new THREE.OrbitControls(camera, renderer.domElement);
          controls.enableDamping = true;
          controls.dampingFactor = 0.05;
          controls.autoRotate = true;
          controls.autoRotateSpeed = 0.6;
          controls.target.set(0, 0, 0);

          // 光源
          var ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
          scene.add(ambientLight);

          // ==========================================
          // 视觉升级 1：全息防御光盾 (Steiner 阶段激活)
          // ==========================================
          if (steinerLines.length > 0) {{
              var shieldGeom = new THREE.SphereGeometry(95, 32, 32);
              var shieldMat = new THREE.MeshBasicMaterial({{
                  color: 0x00eaff,
                  wireframe: true,
                  transparent: true,
                  opacity: 0.03,
                  blending: THREE.AdditiveBlending
              }});
              scene.add(new THREE.Mesh(shieldGeom, shieldMat));

              var outerShieldGeom = new THREE.SphereGeometry(180, 16, 16);
              var outerShieldMat = new THREE.MeshBasicMaterial({{
                  color: 0x00eaff,
                  wireframe: true,
                  transparent: true,
                  opacity: 0.01
              }});
              scene.add(new THREE.Mesh(outerShieldGeom, outerShieldMat));
          }}

          // ==========================================
          // 视觉升级 2：强化线条对比度 (激光防线质感)
          // ==========================================
          function addLines(linesData, colorHex, opacity) {{
            if (!linesData || linesData.length === 0) return;
            var vertices = [];
            linesData.forEach(function(line) {{
              if (line.length >= 2) {{
                vertices.push(line[0][0], line[0][1], line[0][2], line[1][0], line[1][1], line[1][2]);
              }}
            }});
            var geometry = new THREE.BufferGeometry();
            geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
            var material = new THREE.LineBasicMaterial({{
                color: colorHex,
                opacity: opacity,
                transparent: true,
                blending: THREE.AdditiveBlending
            }});
            scene.add(new THREE.LineSegments(geometry, material));
          }}

          if (steinerLines.length > 0) {{
              addLines(normalLines, 0x5c8cbe, 0.04);
              addLines(steinerLines, 0x00eaff, 0.95);
          }} else {{
              addLines(normalLines, 0x5c8cbe, 0.18);
          }}

          // ==========================================
          // 构建 Node Meshes（支持光线拾取）
          // ==========================================
          var nodeMeshes = [];
          var sphereGeom = new THREE.SphereGeometry(1, 16, 16);

          nodesData.forEach(function(node, index) {{
              var colorStr = node.itemStyle.color;
              var mat = new THREE.MeshBasicMaterial({{
                  color: new THREE.Color(colorStr),
                  transparent: true,
                  opacity: node.itemStyle.opacity
              }});
              var mesh = new THREE.Mesh(sphereGeom, mat);
              mesh.position.set(node.value[0], node.value[1], node.value[2]);
              var scale = node.symbolSize * 0.4;
              mesh.scale.setScalar(scale);
              mesh.userData = {{ baseScale: scale, data: node }};
              scene.add(mesh);
              nodeMeshes.push(mesh);
          }});

          // ==========================================
          // Raycaster 拾取逻辑
          // ==========================================
          var raycaster = new THREE.Raycaster();
          var mouse = new THREE.Vector2();
          var hoveredMesh = null;

          container.addEventListener('mousemove', function(event) {{
              var rect = container.getBoundingClientRect();
              mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
              mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

              raycaster.setFromCamera(mouse, camera);
              var intersects = raycaster.intersectObjects(nodeMeshes);

              if (intersects.length > 0) {{
                  if (hoveredMesh !== intersects[0].object) {{
                      if (hoveredMesh) hoveredMesh.scale.setScalar(hoveredMesh.userData.baseScale);
                      hoveredMesh = intersects[0].object;
                      hoveredMesh.scale.setScalar(hoveredMesh.userData.baseScale * 1.5);
                  }}

                  var node = hoveredMesh.userData.data;
                  var statusColor = node.status.includes('Honeypot') ? '#EF4444' : '#10B981';

                  var tHtml = '<div class="tt-header">NODE ID: ' + node.name + '</div>';
                  tHtml += '<div class="tt-row"><span class="tt-label">IP Address</span> <span class="tt-value">' + node.ip + '</span></div>';
                  tHtml += '<div class="tt-row"><span class="tt-label">Network Layer</span> <span class="tt-value" style="text-transform: capitalize;">' + node.layer + '</span></div>';
                  tHtml += '<div class="tt-row"><span class="tt-label">Security Status</span> <span class="tt-value" style="color:' + statusColor + ';">' + node.status + '</span></div>';

                  tooltip.innerHTML = tHtml;
                  tooltip.style.display = 'block';
                  tooltip.style.left = (event.clientX + 15) + 'px';
                  tooltip.style.top = (event.clientY + 15) + 'px';
                  document.body.style.cursor = 'pointer';
              }} else {{
                  if (hoveredMesh) {{
                      hoveredMesh.scale.setScalar(hoveredMesh.userData.baseScale);
                      hoveredMesh = null;
                  }}
                  tooltip.style.display = 'none';
                  document.body.style.cursor = 'default';
              }}
          }});

          // ==========================================
          // 视觉升级 3：攻击粒子动画 (沿 Steiner 路径飞行)
          // ==========================================
          if (attackPath.length > 1) {{
              // 显示攻击警报
              document.getElementById('attack-alert').style.display = 'block';

              // 构建路径坐标
              var nodeMap = {{}};
              nodesData.forEach(function(n) {{ nodeMap[n.id] = n.value; }});

              var pathCoords = [];
              attackPath.forEach(function(id) {{
                  if (nodeMap[id]) pathCoords.push(nodeMap[id].slice());
              }});

              if (pathCoords.length >= 2) {{
                  // 生成插值帧
                  var frames = [];
                  var stepsPerSeg = Math.ceil(40 / (pathCoords.length - 1));
                  for (var seg = 0; seg < pathCoords.length - 1; seg++) {{
                      var p1 = pathCoords[seg], p2 = pathCoords[seg+1];
                      for (var f = 0; f < stepsPerSeg; f++) {{
                          var t = f / Math.max(stepsPerSeg-1, 1);
                          var ease = t*t*(3-2*t);
                          frames.push([
                              p1[0] + (p2[0]-p1[0])*ease,
                              p1[1] + (p2[1]-p1[1])*ease,
                              p1[2] + (p2[2]-p1[2])*ease
                          ]);
                      }}
                  }}

                  // 创建攻击粒子 (发光球体)
                  var particleGeom = new THREE.SphereGeometry(1, 8, 8);
                  var particleMat = new THREE.MeshBasicMaterial({{
                      color: 0xEF4444,
                      transparent: true,
                      opacity: 1.0
                  }});
                  var particle = new THREE.Mesh(particleGeom, particleMat);
                  particle.scale.setScalar(8);
                  scene.add(particle);

                  // 粒子光晕
                  var glowGeom = new THREE.SphereGeometry(1, 8, 8);
                  var glowMat = new THREE.MeshBasicMaterial({{
                      color: 0xEF4444,
                      transparent: true,
                      opacity: 0.3,
                      blending: THREE.AdditiveBlending
                  }});
                  var glow = new THREE.Mesh(glowGeom, glowMat);
                  glow.scale.setScalar(18);
                  scene.add(glow);

                  // 路径轨迹线 (红色虚线感)
                  var trailVertices = [];
                  frames.forEach(function(pos) {{
                      trailVertices.push(pos[0], pos[1], pos[2]);
                  }});
                  var trailGeom = new THREE.BufferGeometry();
                  trailGeom.setAttribute('position', new THREE.Float32BufferAttribute(trailVertices, 3));
                  var trailMat = new THREE.LineBasicMaterial({{
                      color: 0xEF4444,
                      transparent: true,
                      opacity: 0.15
                  }});
                  scene.add(new THREE.Line(trailGeom, trailMat));

                  // 动画循环
                  var frameIdx = 0;
                  function animateParticle() {{
                      if (frameIdx >= frames.length) {{
                          // 到达目标 - 蜜罐拦截特效
                          var impactPos = pathCoords[pathCoords.length-1];
                          particle.position.set(impactPos[0], impactPos[1], impactPos[2]);
                          glow.position.set(impactPos[0], impactPos[1], impactPos[2]);

                          // 拦截闪光
                          var flashGeom = new THREE.SphereGeometry(1, 16, 16);
                          var flashMat = new THREE.MeshBasicMaterial({{
                              color: 0x10B981,
                              transparent: true,
                              opacity: 0.6,
                              blending: THREE.AdditiveBlending
                          }});
                          var flash = new THREE.Mesh(flashGeom, flashMat);
                          flash.position.set(impactPos[0], impactPos[1], impactPos[2]);
                          flash.scale.setScalar(30);
                          scene.add(flash);

                          // 闪光动画
                          var flashFrame = 0;
                          function animateFlash() {{
                              if (flashFrame > 30) {{
                                  scene.remove(flash);
                                  return;
                              }}
                              flash.scale.setScalar(30 + flashFrame * 2);
                              flashMat.opacity = 0.6 * (1 - flashFrame / 30);
                              flashFrame++;
                              requestAnimationFrame(animateFlash);
                          }}
                          animateFlash();

                          // 更新警报文字
                          document.getElementById('attack-alert').innerHTML = 'Threat Neutralized : Honeypot Intercepted';
                          document.getElementById('attack-alert').style.borderColor = '#10B981';
                          document.getElementById('attack-alert').style.color = '#10B981';
                          document.getElementById('attack-alert').style.background = 'rgba(16, 185, 129, 0.15)';
                          return;
                      }}

                      var pos = frames[frameIdx];
                      particle.position.set(pos[0], pos[1], pos[2]);
                      glow.position.set(pos[0], pos[1], pos[2]);
                      frameIdx++;
                      requestAnimationFrame(animateParticle);
                  }}
                  animateParticle();
              }}
          }}

          // ==========================================
          // 主渲染循环
          // ==========================================
          function animate() {{
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
          }}
          animate();

          window.addEventListener('resize', function() {{
            var w = container.clientWidth;
            var h = container.clientHeight;
            camera.aspect = w / h;
            camera.updateProjectionMatrix();
            renderer.setSize(w, h);
          }});
      }}
      initThree();
    }})();
  </script>
</body>
</html>"""


