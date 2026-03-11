from falkordb import FalkorDB

# Verbinde zu FalkorDB
db = FalkorDB(host='127.0.0.1', port=6379)
graph = db.select_graph('openclaw_ontology')

# Test: Einen Knoten erstellen
query = """
CREATE (p:Person {name: 'Alex', role: 'Admin'})
RETURN p
"""
result = graph.query(query)

# Test: Den Knoten abfragen
query = """
MATCH (p:Person {name: 'Alex'})
RETURN p.name, p.role
"""
result = graph.query(query)

for record in result.result_set:
    print(f"Erfolgreich aus FalkorDB gelesen: {record[0]} ({record[1]})")
