import json

file_path = r'c:\Users\thita\docker\workflows\ParallelSubWorkflow.json'

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 1. Find and replace "All Done" node
nodes = data.get('nodes', [])
new_node = {
    "parameters": {
        "workflowId": {
            "__rl": True,
            "value": "mZffE3wZjSPvaiRf",
            "mode": "list",
            "cachedResultName": "Compare"
        },
        "workflowInputs": {
            "mappingMode": "defineBelow",
            "value": {
                "body": {
                    "schema": "={{ $('Start').first().json.directory }}"
                }
            },
            "matchingColumns": [],
            "schema": [],
            "attemptToConvertTypes": False,
            "convertFieldsToString": True
        },
        "options": {}
    },
    "type": "n8n-nodes-base.executeWorkflow",
    "typeVersion": 1.2,
    "position": [
        2400,
        0
    ],
    "id": "execute-compare-node",
    "name": "Trigger Compare Workflow"
}

node_replaced = False
for i, node in enumerate(nodes):
    if node.get('name') == 'All Done':
        nodes[i] = new_node
        node_replaced = True
        break

if not node_replaced:
    print("Error: 'All Done' node not found.")
else:
    print("'All Done' node replaced.")

# 2. Update connections
connections = data.get('connections', {})
check_completion = connections.get('Check Completion', {})
main_conn = check_completion.get('main', [])

conn_updated = False
if main_conn:
    # main_conn is list of lists of items
    for sublist in main_conn:
        for item in sublist:
            if item.get('node') == 'All Done':
                item['node'] = 'Trigger Compare Workflow'
                conn_updated = True

if conn_updated:
    print("Connections updated.")
else:
    print("Error: Connection to 'All Done' not found.")

# Write back
with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

print("File saved.")
