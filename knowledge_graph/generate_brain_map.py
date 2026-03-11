#!/usr/bin/env python3
import json
from falkordb import FalkorDB

# --- Konfiguration ---
FALKOR_HOST = "127.0.0.1"
FALKOR_PORT = 6379
GRAPH_NAME = "openclaw_ontology"
OUTPUT_FILE = "/home/clawdi/.openclaw/workspace/openclaw-memory/index.html"

def generate_map():
    db = FalkorDB(host=FALKOR_HOST, port=FALKOR_PORT)
    graph = db.select_graph(GRAPH_NAME)
    
    # 1. Alle Knoten laden
    nodes_res = graph.query("MATCH (n) RETURN n, labels(n)[0]")
    cy_nodes = []
    for record in nodes_res.result_set:
        node = record[0]
        label = record[1]
        name = node.properties.get('name', node.properties.get('id', 'Unknown'))
        cy_nodes.append({
            "data": {
                "id": str(node.id),
                "label": f"{label}: {name}",
                "type": label
            }
        })
    
    # 2. Alle Beziehungen laden
    edges_res = graph.query("MATCH (n)-[r]->(m) RETURN id(n), type(r), id(m)")
    cy_edges = []
    for record in edges_res.result_set:
        cy_edges.append({
            "data": {
                "source": str(record[0]),
                "target": str(record[2]),
                "label": record[1]
            }
        })

    # 3. HTML Template mit Cytoscape.js bauen
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Clawdi Brain Dashboard</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js"></script>
        <style>
            body {{ font-family: sans-serif; margin: 0; background: #1a1a1a; color: white; overflow: hidden; }}
            #cy {{ width: 100vw; height: 90vh; display: block; }}
            .header {{ padding: 20px; background: #2c3e50; box-shadow: 0 2px 10px rgba(0,0,0,0.5); display: flex; justify-content: space-between; align-items: center; }}
            .stats {{ font-size: 0.9em; opacity: 0.8; }}
            h1 {{ margin: 0; font-size: 1.5em; color: #3498db; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div>
                <h1>🧠 Clawdi Brain Map</h1>
                <div class="stats">Graph: {GRAPH_NAME} | Nodes: {len(cy_nodes)} | Edges: {len(cy_edges)}</div>
            </div>
            <div>
                <button onclick="window.location.reload()">Refresh</button>
            </div>
        </div>
        <div id="cy"></div>
        <script>
            var cy = cytoscape({{
                container: document.getElementById('cy'),
                elements: {{
                    nodes: {json.dumps(cy_nodes)},
                    edges: {json.dumps(cy_edges)}
                }},
                style: [
                    {{
                        selector: 'node',
                        style: {{
                            'background-color': '#3498db',
                            'label': 'data(label)',
                            'color': '#fff',
                            'text-valign': 'center',
                            'text-halign': 'center',
                            'font-size': '10px',
                            'width': '60px',
                            'height': '60px',
                            'text-wrap': 'wrap',
                            'text-max-width': '50px'
                        }}
                    }},
                    {{
                        selector: 'node[type="Person"]',
                        style: {{ 'background-color': '#e74c3c' }}
                    }},
                    {{
                        selector: 'node[type="Project"]',
                        style: {{ 'background-color': '#f1c40f', 'width': '80px', 'height': '80px' }}
                    }},
                    {{
                        selector: 'edge',
                        style: {{
                            'width': 2,
                            'line-color': '#555',
                            'target-arrow-color': '#555',
                            'target-arrow-shape': 'triangle',
                            'curve-style': 'bezier',
                            'label': 'data(label)',
                            'font-size': '8px',
                            'color': '#aaa',
                            'text-rotation': 'autorotate'
                        }}
                    }}
                ],
                layout: {{
                    name: 'cose',
                    animate: true
                }}
            }});
        </script>
    </body>
    </html>
    """
    
    with open(OUTPUT_FILE, "w") as f:
        f.write(html_content)
    print(f"Brain Map generiert: {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_map()
