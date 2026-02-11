from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Dict, Any
try:
    import langgraph  # optional real LangGraph
    LANGGRAPH_AVAILABLE = True
except Exception:
    LANGGRAPH_AVAILABLE = False

class LangGraphAdapter:
    def __init__(self):
        self.nodes: Dict[str, Callable[..., Any]] = {}

    def add_node(self, name: str, fn: Callable[..., Any]):
        self.nodes[name] = fn

    def run_nodes_parallel(self, calls: Dict[str, Dict[str, Any]], max_workers:int=4) -> Dict[str, Any]:
        """
        Execute registered node callables in parallel and return results mapping node_name -> result.
        This is a simple adapter to demonstrate LangGraph-style coordination.
        """
        results = {}
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {}
            for node_name, kwargs in calls.items():
                fn = self.nodes.get(node_name)
                if not fn:
                    results[node_name] = {"error": "node not registered"}
                    continue
                futures[ex.submit(fn, **kwargs)] = node_name
            for future in futures:
                node_name = futures[future]
                try:
                    results[node_name] = future.result(timeout=30)
                except Exception as e:
                    results[node_name] = {"error": str(e)}
        return results
