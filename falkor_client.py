#!/usr/bin/env python3
"""
falkor_client.py – Graph Database Client for Clawdi AI Memory
==============================================================

Provides an interface to FalkorDB (graph DB) for managing entities
and their relationships via Cypher queries.

Usage:
    python falkor_client.py create-node Person '{"name": "Alex", "role": "Admin"}'
    python falkor_client.py relate Alex HAS_BFF Laura
    python falkor_client.py query "MATCH (n) RETURN n"
"""

import argparse
import json
import logging
import sys
from typing import Any, Dict, List, Optional

from falkordb import FalkorDB

# ── Configuration ──────────────────────────────────────────────────────────

FALKOR_HOST = "127.0.0.1"
FALKOR_PORT = 6379
GRAPH_NAME = "openclaw_ontology"

# ── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("falkor_client")

# ── Client Class ──────────────────────────────────────────────────────────

class FalkorMemory:
    """Wrapper for FalkorDB interactions."""

    def __init__(self, host: str = FALKOR_HOST, port: int = FALKOR_PORT, graph_name: str = GRAPH_NAME):
        try:
            self.db = FalkorDB(host=host, port=port)
            self.graph = self.db.select_graph(graph_name)
            log.debug(f"Connected to FalkorDB at {host}:{port}, graph: {graph_name}")
        except Exception as e:
            log.error(f"Connection to FalkorDB failed: {e}")
            sys.exit(1)

    def query(self, cypher: str) -> List[Any]:
        """Executes a Cypher query and returns the result."""
        try:
            log.debug(f"Query: {cypher}")
            result = self.graph.query(cypher)
            return result.result_set
        except Exception as e:
            log.error(f"Cypher query error: {e}")
            return []

    def create_node(self, label: str, properties: Dict[str, Any]):
        """Creates a new node."""
        props_str = ", ".join([f"{k}: '{v}'" if isinstance(v, str) else f"{k}: {v}" for k, v in properties.items()])
        cypher = f"CREATE (n:{label} {{{props_str}}}) RETURN n"
        return self.query(cypher)

    def relate(self, from_node_name: str, relation: str, to_node_name: str, properties: Optional[Dict[str, Any]] = None):
        """Creates a relationship between two nodes (based on the 'name' attribute)."""
        props_str = ""
        if properties:
            p_list = [f"{k}: '{v}'" if isinstance(v, str) else f"{k}: {v}" for k, v in properties.items()]
            props_str = f" {{{', '.join(p_list)}}}"
            
        cypher = f"""
        MATCH (a {{name: '{from_node_name}'}}), (b {{name: '{to_node_name}'}})
        CREATE (a)-[r:{relation}{props_str}]->(b)
        RETURN r
        """
        return self.query(cypher)

    def get_all_nodes(self):
        """Returns all nodes in the graph."""
        return self.query("MATCH (n) RETURN n")

# ── CLI Interface ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Clawdi FalkorDB CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Create Node
    node_parser = subparsers.add_parser("create-node")
    node_parser.add_argument("label", help="e.g. Person, Project, Task")
    node_parser.add_argument("props", help="JSON string of properties")

    # Relate
    rel_parser = subparsers.add_parser("relate")
    rel_parser.add_argument("from_name")
    rel_parser.add_argument("type", help="e.g. HAS_BFF, WORKS_ON")
    rel_parser.add_argument("to_name")

    # Raw Query
    query_parser = subparsers.add_parser("query")
    query_parser.add_argument("cypher")

    args = parser.parse_args()
    client = FalkorMemory()

    if args.command == "create-node":
        props = json.loads(args.props)
        client.create_node(args.label, props)
        print(f"Node ({args.label}) created.")
    
    elif args.command == "relate":
        client.relate(args.from_name, args.type, args.to_name)
        print(f"Relationship {args.type} created: {args.from_name} -> {args.to_name}")

    elif args.command == "query":
        res = client.query(args.cypher)
        for r in res:
            print(r)

if __name__ == "__main__":
    main()
