import os
import json 
import subprocess 
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

class GraphifyVaultManager:
    def __init__(
        self,
        vault_path: str = "./vault",
        output_dir: Optional[str] = None,
        ensure_dirs: bool = True,
    ):
        self.vault_path = Path(vault_path).resolve()
        # Graphify typically outputs graph artifacts into a target directory (defaults to vault/.graphify)
        self.output_dir = Path(output_dir).resolve() if output_dir else self.vault_path / ".graphify"
        self.graph_json_path = self.output_dir / "graph.json"

        if ensure_dirs:
            self.vault_path.mkdir(parents=True, exist_ok=True)
            self.output_dir.mkdir(parents=True, exist_ok=True)

    def _build_local_vault_graph(self) -> Dict[str, Any]:
        """
        Fast local fallback parser extracting wikilinks and YAML frontmatter directly from Obsidian Markdown files.
        Runs 100% offline with zero external dependencies and zero LLM calls.
        """
        import re
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []
        node_ids = set()

        if not self.vault_path.exists():
            return {"nodes": [], "edges": []}

        for md_path in self.vault_path.rglob("*.md"):
            if not md_path.is_file() or md_path.name.startswith("."):
                continue
            rel_path = md_path.relative_to(self.vault_path).as_posix()
            stem = md_path.stem
            node_id = stem

            content = ""
            properties: Dict[str, Any] = {}
            label = stem
            tags: List[str] = []
            domain: Optional[str] = None
            action: Optional[str] = None
            try:
                content = md_path.read_text(encoding="utf-8", errors="ignore")
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        frontmatter_raw = parts[1]
                        parsed_yaml = None
                        try:
                            import yaml
                            parsed_yaml = yaml.safe_load(frontmatter_raw)
                        except Exception:
                            parsed_yaml = None

                        if isinstance(parsed_yaml, dict):
                            properties = {str(k): v for k, v in parsed_yaml.items()}
                        else:
                            current_list_key = None
                            for line in frontmatter_raw.splitlines():
                                stripped = line.strip()
                                if not stripped:
                                    continue
                                if stripped.startswith("- ") and current_list_key:
                                    item = stripped[2:].strip().strip("'\"")
                                    if item:
                                        properties.setdefault(current_list_key, []).append(item)
                                elif ":" in line:
                                    k, v = line.split(":", 1)
                                    k = k.strip()
                                    v = v.strip().strip("'\"")
                                    if v.startswith("[") and v.endswith("]"):
                                        items = [i.strip().strip("'\"") for i in v[1:-1].split(",") if i.strip()]
                                        properties[k] = items
                                        current_list_key = None
                                    elif not v:
                                        current_list_key = k
                                        properties[k] = []
                                    else:
                                        properties[k] = v
                                        current_list_key = None

                        if "id" in properties and str(properties["id"]).strip():
                            node_id = str(properties["id"]).strip()

                        raw_tags = properties.get("tags", [])
                        if isinstance(raw_tags, list):
                            tags = [str(t).strip().strip("'\"").lower() for t in raw_tags if str(t).strip()]
                        elif isinstance(raw_tags, str):
                            cleaned = raw_tags.strip().strip("[]")
                            if cleaned:
                                tags = [t.strip().strip("'\"").lower() for t in cleaned.split(",") if t.strip()]

                        if "domain" in properties and properties["domain"]:
                            domain = str(properties["domain"]).strip().lower()
                        if "action" in properties and properties["action"]:
                            action = str(properties["action"]).strip().lower()

                for line in content.splitlines():
                    if line.startswith("# "):
                        label = line[2:].strip()
                        break
            except Exception:
                pass

            if node_id not in node_ids:
                node_ids.add(node_id)
                node_entry: Dict[str, Any] = {
                    "id": node_id,
                    "label": label,
                    "source_file": rel_path,
                    "properties": properties,
                    "tags": tags,
                }
                if domain:
                    node_entry["domain"] = domain
                if action:
                    node_entry["action"] = action
                nodes.append(node_entry)

            targets = re.findall(r'\[\[(.*?)\]\]', content)
            for target in targets:
                clean_target = target.split("|")[0].strip()
                if clean_target:
                    edges.append({
                        "source": node_id,
                        "target": clean_target,
                    })

        graph_data = {"nodes": nodes, "edges": edges}
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            with open(self.graph_json_path, "w", encoding="utf-8") as f:
                json.dump(graph_data, f, indent=2)
        except Exception:
            pass
        return graph_data

    def build_graph(self, incremental: bool = True) -> bool:
        """
        Triggers the graphify CLI to parse the Obsidian vault, falling back to local wikilink graph parsing if unavailable.
        """
        if not self.vault_path.exists():
            raise FileNotFoundError(f"Vault path does not exist: {self.vault_path}")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            sys.executable, "-m", "graphify", "extract", str(self.vault_path),
            "--no-cluster", "--no-gitignore", "--out", str(self.output_dir)
        ]
        if not incremental:
            cmd.append("--force")
        environment = {**os.environ, "GRAPHIFY_OUT": str(self.output_dir)}

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                env=environment,
                timeout=60,
            )
            if self.graph_json_path.is_file():
                return True
        except subprocess.TimeoutExpired:
            if os.environ.get("BUILDRELAY_DEBUG"):
                print("[GraphifyTool Error] Graph build timed out after 60 seconds")
        except subprocess.CalledProcessError as e:
            if os.environ.get("BUILDRELAY_DEBUG"):
                print(f"[GraphifyTool Error] Subprocess failed with code {e.returncode}")
                print(f"Stdout: {e.stdout}")
                print(f"Stderr: {e.stderr}")
            else:
                debug_log = self.output_dir.parent / ".state" / "graphify_debug.log"
                try:
                    debug_log.parent.mkdir(parents=True, exist_ok=True)
                    debug_log.write_text(
                        f"Return code: {e.returncode}\n--- stdout ---\n{e.stdout}\n--- stderr ---\n{e.stderr}",
                        encoding="utf-8",
                    )
                except Exception:
                    pass
        except Exception:
            pass

        # Robust local vault fallback parser
        fallback_data = self._build_local_vault_graph()
        return bool(fallback_data.get("nodes"))

    def load_graph(self) -> Dict[str, Any]:
        """
        Loads the generated graph.json structure into memory for traversal.
        """
        if not self.graph_json_path.exists():
            from tools.ui import print_tool_call
            print_tool_call("orchestrator", "Graphify", f"Indexing knowledge graph at {self.output_dir.name}...")
            success = self.build_graph(incremental=False)
            if not success or not self.graph_json_path.exists():
                return self._build_local_vault_graph()

        try:
            with open(self.graph_json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"[GraphifyTool Error] Failed to parse graph.json: {e}")
            return {"nodes": [], "edges": []}

    def query_nodes(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Searches nodes in the graph matching a keyword (useful for finding tasks or specs).
        """
        data = self.load_graph()
        nodes = data.get("nodes", [])
        term = search_term.lower()
        
        matches = [
            node for node in nodes 
            if any(term in str(node.get(key, "")).lower()
                   for key in ("id", "label", "source_file", "properties", "tags", "domain", "action"))
        ]
        return matches

    def query_by_keywords(
        self,
        keywords: List[str] | str,
        top_k: int = 5,
        min_score: float = 0.15,
    ) -> List[tuple[Dict[str, Any], float]]:
        """
        Ranks graph nodes by keyword overlap relevance using weighted attribute scoring.
        Weights:
          - Tag exact match: 3.0
          - Domain exact match: 2.5
          - ID / Target match: 2.0
          - Label / Title match: 1.5
          - Content / Property match: 1.0

        Computes weighted overlap normalized against total query keyword count.
        Returns up to top_k nodes exceeding min_score, sorted descending by score.
        """
        import re
        if isinstance(keywords, str):
            from tools.taxonomy import extract_keywords
            keywords = extract_keywords(keywords)

        query_kw = [k.strip().lower() for k in keywords if k and k.strip()]
        if not query_kw:
            return []

        data = self.load_graph()
        nodes = data.get("nodes", [])
        scored: List[tuple[Dict[str, Any], float]] = []

        for node in nodes:
            # Extract tags
            node_tags: List[str] = []
            raw_tags = node.get("tags")
            if raw_tags is None and isinstance(node.get("properties"), dict):
                raw_tags = node["properties"].get("tags")
            if isinstance(raw_tags, list):
                node_tags = [str(t).strip().strip("'\"").lower() for t in raw_tags if str(t).strip()]
            elif isinstance(raw_tags, str):
                cleaned = raw_tags.strip().strip("[]")
                if cleaned:
                    node_tags = [t.strip().strip("'\"").lower() for t in cleaned.split(",") if t.strip()]

            # Extract domain, action, id, target, label
            node_domain = str(node.get("domain") or (node.get("properties") or {}).get("domain") or "").strip().lower()
            node_action = str(node.get("action") or (node.get("properties") or {}).get("action") or "").strip().lower()
            node_id = str(node.get("id") or "").strip().lower()
            node_target = str((node.get("properties") or {}).get("target") or node.get("target") or "").strip().lower()
            node_label = str(node.get("label") or "").strip().lower()

            # Pre-tokenize id, target, label for matching
            id_tokens = set(re.findall(r"[a-z0-9]+", node_id))
            target_tokens = set(re.findall(r"[a-z0-9]+", node_target))
            label_tokens = set(re.findall(r"[a-z0-9]+", node_label))

            # Other properties / content
            props = node.get("properties")
            props_text = ""
            if isinstance(props, dict):
                other_vals = [
                    str(v) for k, v in props.items()
                    if k not in ("tags", "domain", "action", "id", "target")
                ]
                props_text = " ".join(other_vals).lower()
            elif isinstance(props, str):
                props_text = props.lower()
            source_file = str(node.get("source_file") or "").lower()
            content_str = str(node.get("content") or "").lower()
            combined_other = f"{props_text} {source_file} {content_str}"

            node_score = 0.0
            for kw in query_kw:
                # 1. Tag exact match (3.0)
                if any(kw == t or kw in t.split("-") or kw in t.split("_") for t in node_tags):
                    node_score += 3.0

                # 2. Domain exact match (2.5)
                if node_domain and (kw == node_domain or kw in node_domain.split("-")):
                    node_score += 2.5

                # 3. ID / Target match (2.0)
                if kw in id_tokens or kw in target_tokens or (node_target and kw in node_target):
                    node_score += 2.0

                # 4. Label / Title match (1.5)
                if kw in label_tokens or kw in node_label:
                    node_score += 1.5

                # 5. Content / Property match (1.0)
                if kw in combined_other:
                    node_score += 1.0

            # Normalize: max potential weight per keyword is 10.0
            norm_score = min(1.0, round(node_score / (10.0 * len(query_kw)), 4))
            if norm_score >= min_score:
                scored.append((node, norm_score))

        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:top_k]

    def get_neighbors(self, node_id: str) -> List[Dict[str, Any]]:
        """
        Finds direct downstream/upstream connected nodes (useful for checking related research or specs).
        """
        data = self.load_graph()
        edges = data.get("edges", [])
        nodes = {n.get("id"): n for n in data.get("nodes", [])}
        
        neighbor_ids = set()
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            if source == node_id:
                neighbor_ids.add(target)
            elif target == node_id:
                neighbor_ids.add(source)
                
        return [nodes[nid] for nid in neighbor_ids if nid in nodes]

    def resolve_note_sources(self, nodes: List[Dict[str, Any]]) -> list[str]:
        """Resolve Graphify source files to existing Markdown paths within this vault."""
        sources = set()
        for node in nodes:
            properties = node.get("properties")
            properties = properties if isinstance(properties, dict) else {}
            source = node.get("source_file") or properties.get("source_file")
            if not isinstance(source, str) or not source.strip():
                continue
            try:
                path = Path(source)
                path = (self.vault_path / path).resolve() if not path.is_absolute() else path.resolve()
                if path.is_relative_to(self.vault_path) and path.suffix.lower() == ".md" and path.is_file():
                    sources.add(path.relative_to(self.vault_path).as_posix())
            except (OSError, ValueError, RuntimeError):
                # Stale or malformed graph paths must not prevent saving a report.
                continue
        return sorted(sources)

# Reference to unbound method for explicit testing when mocked in fixtures
_original_build_graph = GraphifyVaultManager.build_graph

# Quick standalone test execution block
if __name__ == "__main__":
    manager = GraphifyVaultManager()
    print("Testing GraphifyVaultManager initialization...")
    manager.build_graph(incremental=False)
