import json
import uuid

def create_uuid():
    return str(uuid.uuid4())

def main():
    file_path = r"C:\Users\thita\docker\workflows\RDVATLookup.json"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    # 1. Update Workflow Name
    workflow['name'] = "RD VAT Lookup"

    # 2. Update HTTP Request Node
    for node in workflow['nodes']:
        if node['name'] == "HTTP: RD VAT lookup (buyer)":
            node['name'] = "HTTP: RD VAT lookup"
            # Replace buyer_vat_id/branch with generic vat_id/branch_id
            node['parameters']['body'] = node['parameters']['body'].replace("buyer_vat_id", "vat_id").replace("buyer_branch", "branch_id")
        
        if node['name'] == "Upsert VAT company (buyer)":
            node['name'] = "Upsert VAT company"

        if node['name'] == "Normalize RD response (buyer)":
            node['name'] = "Normalize RD response"

    # 3. Create New Nodes
    
    # Node: Route Type (Success)
    route_success_id = create_uuid()
    route_success_node = {
        "parameters": {
            "conditions": {
                "options": {
                    "caseSensitive": True,
                    "leftValue": "",
                    "typeValidation": "strict",
                    "version": 2
                },
                "conditions": [
                    {
                        "id": create_uuid(),
                        "leftValue": "={{ $json.type }}",
                        "rightValue": "buyer",
                        "operator": {
                            "type": "string",
                            "operation": "equals"
                        }
                    }
                ],
                "combinator": "and"
            },
            "options": {}
        },
        "type": "n8n-nodes-base.if",
        "typeVersion": 2.2,
        "position": [-1200, -50], # Adjust position
        "id": route_success_id,
        "name": "Route Type (Success)"
    }

    # Node: Route Type (Failure)
    route_failure_id = create_uuid()
    route_failure_node = {
        "parameters": {
            "conditions": {
                "options": {
                    "caseSensitive": True,
                    "leftValue": "",
                    "typeValidation": "strict",
                    "version": 2
                },
                "conditions": [
                    {
                        "id": create_uuid(),
                        "leftValue": "={{ $json.type }}",
                        "rightValue": "buyer",
                        "operator": {
                            "type": "string",
                            "operation": "equals"
                        }
                    }
                ],
                "combinator": "and"
            },
            "options": {}
        },
        "type": "n8n-nodes-base.if",
        "typeVersion": 2.2,
        "position": [-800, 200], # Adjust position
        "id": route_failure_id,
        "name": "Route Type (Failure)"
    }

    # Node: Mark vendor_vat_id_info_status=true
    vendor_success_id = create_uuid()
    vendor_success_node = {
        "parameters": {
            "operation": "update",
            "schema": {"__rl": True, "value": "public", "mode": "name"},
            "table": {"__rl": True, "value": "invoice_check_summary", "mode": "list", "cachedResultName": "invoice_check_summary"},
            "columns": {
                "mappingMode": "defineBelow",
                "value": {
                    "vendor_vat_id_info_status": "={{ true }}",
                    "invoice_number": "={{ $json.invoice_number }}"
                },
                "matchingColumns": ["invoice_number"]
            },
            "options": {}
        },
        "type": "n8n-nodes-base.postgres",
        "typeVersion": 2.6,
        "position": [-600, -400],
        "id": vendor_success_id,
        "name": "Mark vendor_vat_id_info_status=true",
        "credentials": {"postgres": {"id": "59xvxQayjivgQ1fN", "name": "Postgres account 3"}}
    }

    # Node: Mark vendor_vat_id_info_status=false
    vendor_failure_id = create_uuid()
    vendor_failure_node = {
        "parameters": {
            "operation": "update",
            "schema": {"__rl": True, "value": "public", "mode": "name"},
            "table": {"__rl": True, "value": "invoice_check_summary", "mode": "list", "cachedResultName": "invoice_check_summary"},
            "columns": {
                "mappingMode": "defineBelow",
                "value": {
                    "vendor_vat_id_info_status": "={{ false }}",
                    "invoice_number": "={{ $json.invoice_number }}"
                },
                "matchingColumns": ["invoice_number"]
            },
            "options": {}
        },
        "type": "n8n-nodes-base.postgres",
        "typeVersion": 2.6,
        "position": [-600, 300],
        "id": vendor_failure_id,
        "name": "Mark vendor_vat_id_info_status=false",
        "credentials": {"postgres": {"id": "59xvxQayjivgQ1fN", "name": "Postgres account 3"}}
    }

    workflow['nodes'].extend([route_success_node, route_failure_node, vendor_success_node, vendor_failure_node])

    # 4. Update Connections
    
    # Helper to find node by name
    def get_node_name(name):
        for n in workflow['nodes']:
            if n['name'] == name:
                return n['name']
        return None

    # Disconnect old connections
    # "Branch: RD lookup success" -> "Compare buyer address vs RD"
    # "Branch: RD lookup failed" -> "Mark buyer_vat_info_status=false"
    
    # We will rebuild the connections for the branching nodes
    
    # Connect "Branch: RD lookup success" to "Route Type (Success)"
    workflow['connections']['Branch: RD lookup success']['main'][0] = [
        {
            "node": "Route Type (Success)",
            "type": "main",
            "index": 0
        }
    ]

    # Connect "Branch: RD lookup failed" to "Route Type (Failure)"
    workflow['connections']['Branch: RD lookup failed']['main'][0] = [
        {
            "node": "Route Type (Failure)",
            "type": "main",
            "index": 0
        }
    ]

    # Connect "Route Type (Success)"
    workflow['connections']['Route Type (Success)'] = {
        "main": [
            [ # True (Buyer)
                {
                    "node": "Compare buyer address vs RD",
                    "type": "main",
                    "index": 0
                }
            ],
            [ # False (Vendor)
                {
                    "node": "Mark vendor_vat_id_info_status=true",
                    "type": "main",
                    "index": 0
                }
            ]
        ]
    }

    # Connect "Route Type (Failure)"
    workflow['connections']['Route Type (Failure)'] = {
        "main": [
            [ # True (Buyer)
                {
                    "node": "Mark buyer_vat_info_status=false",
                    "type": "main",
                    "index": 0
                }
            ],
            [ # False (Vendor)
                {
                    "node": "Mark vendor_vat_id_info_status=false",
                    "type": "main",
                    "index": 0
                }
            ]
        ]
    }
    
    # Update keys in connections object to match renamed nodes
    if "HTTP: RD VAT lookup (buyer)" in workflow['connections']:
        workflow['connections']["HTTP: RD VAT lookup"] = workflow['connections'].pop("HTTP: RD VAT lookup (buyer)")
    
    if "Normalize RD response (buyer)" in workflow['connections']:
        workflow['connections']["Normalize RD response"] = workflow['connections'].pop("Normalize RD response (buyer)")
        
    # Also need to update the references inside the connections values if any node names changed
    # "HTTP: RD VAT lookup (buyer)" was connected to "XML to JSON (RD)"
    # "Normalize RD response (buyer)" was connected to "Upsert VAT company (buyer)" and "Compare buyer address vs RD"
    
    # Let's iterate and fix all references
    name_map = {
        "HTTP: RD VAT lookup (buyer)": "HTTP: RD VAT lookup",
        "Upsert VAT company (buyer)": "Upsert VAT company",
        "Normalize RD response (buyer)": "Normalize RD response"
    }

    for node_name, outputs in workflow['connections'].items():
        for output_type, connections in outputs.items():
            for connection_list in connections:
                for connection in connection_list:
                    if connection['node'] in name_map:
                        connection['node'] = name_map[connection['node']]

    # Also rename keys in connections object if they are in name_map (already done above for HTTP and Norm, but Upsert might be a source? No, Upsert is a sink usually, or connects to Merge)
    # Check if Upsert connects to anything. In RDBuyerVATLookup, Upsert connects to "Merge: success payload + caller" (via "Merge" node?)
    # Let's check the file content again.
    # "Upsert VAT company (buyer)" connects to nothing in the `connections` block shown in the previous turn?
    # Wait, let's check the `connections` block in the file I viewed.
    # The file view was truncated. I need to be careful.
    # But usually Upsert connects to a Merge node to continue the flow.
    # In `RDBuyerVATLookup.json`:
    # "Upsert VAT company (buyer)" is NOT in the connections keys in the snippet I saw?
    # Ah, I see "If found vat info2" -> "Insert rows in a table" (Upsert?)
    # The snippet I saw had:
    # "Norm: JSON1" -> "Code in JavaScript" (Normalize?)
    # The names in the `nodes` array were "Upsert VAT company (buyer)", "Normalize RD response (buyer)".
    # But the `connections` object in the snippet had "VAT INFO1", "XML to JSON1", "Norm: JSON1".
    # This implies the `name` property in the `nodes` array might be different from the key in `connections`?
    # NO. n8n uses the `name` property as the key in `connections`.
    # The snippet I saw at the end of the file (lines 1022+) had keys like "VAT INFO1", "Norm: JSON1".
    # BUT the nodes I saw at the beginning (lines 1-800) had names like "HTTP: RD VAT lookup (buyer)".
    # This means the `connections` block I saw in the snippet might be from a DIFFERENT file or I misread it?
    # Let's re-examine the file content of `RDBuyerVATLookup.json`.
    # Lines 1-800 show nodes with names: "HTTP: RD VAT lookup (buyer)", "XML to JSON (RD)", "Normalize RD response (buyer)".
    # Lines 800-1193 show `connections` block.
    # The keys in `connections` are: "VAT INFO1", "XML to JSON1", "Norm: JSON1"...
    # THIS IS STRANGE. The keys in `connections` MUST match the node names.
    # UNLESS the file I viewed (`RDBuyerVATLookup.json`) has a mismatch between node names and connection keys?
    # If so, the workflow would be broken in n8n.
    # OR, the `connections` block I saw was from `ParallelSubWorkflow.json`?
    # Let's check the previous `view_file` output.
    # Step 502: `RDBuyerVATLookup.json` lines 1-800. Node names are "HTTP: RD VAT lookup (buyer)", etc.
    # Step 507: `RDBuyerVATLookup.json` lines 800-1193.
    # The connections block starts at line 1022.
    # Keys: "VAT INFO1", "XML to JSON1".
    # AND "Merge2", "If", "If found vat info2".
    # These names DO NOT MATCH the node names in lines 1-800.
    # This suggests that `RDBuyerVATLookup.json` might have been edited or I am looking at a file that has inconsistent data.
    # OR, the `nodes` array I saw in lines 1-800 is NOT the whole story.
    # Wait. The file has `nodes` array.
    # Let's look at the `nodes` array again.
    # Line 23: "name": "HTTP: RD VAT lookup (buyer)"
    # Line 39: "name": "XML to JSON (RD)"
    # Line 53: "name": "Normalize RD response (buyer)"
    # Line 263: "name": "Upsert VAT company (buyer)"
    # Line 745: "name": "Compare buyer address vs RD"
    
    # Now look at `connections` (Line 1022+):
    # "VAT INFO1" -> "XML to JSON1"
    # "XML to JSON1" -> "Norm: JSON1"
    
    # This is VERY suspicious. It looks like the `connections` block belongs to a different set of nodes.
    # Is it possible that `RDBuyerVATLookup.json` contains *multiple* workflows or I am misinterpreting the JSON?
    # No, it's a standard n8n workflow JSON.
    # If the node names don't match the connection keys, n8n will not show any connections.
    # Maybe the file I read is CORRUPT or I am misreading the file content.
    # Let's check `RDVendorVATLookup.json` (Step 498).
    # Node names: "Trigger: Called by workflow", "Merge: success payload + caller", "Branch: RD lookup failed".
    # I didn't see the connections block for `RDVendorVATLookup.json`.
    
    # Let's look at `RDBuyerVATLookup.json` again.
    # Maybe the nodes "VAT INFO1" etc are *also* in the file, further down?
    # I viewed lines 1-800 and 800-1193.
    # The `nodes` array ends at line 1021.
    # The `connections` block starts at line 1022.
    # The nodes I saw in 1-800 covered the beginning of the array.
    # Let's check if there are other nodes between 800 and 1021.
    # Line 800 is inside "Mark buyer_address_status=false".
    # Line 1013: "name": "Mark buyer_address_status=false".
    # Line 1021: `]`. End of nodes array.
    
    # So the nodes are:
    # - HTTP: RD VAT lookup (buyer)
    # - XML to JSON (RD)
    # - Normalize RD response (buyer)
    # - Merge: caller + RD response
    # - Branch: RD lookup failed
    # - Branch: RD lookup success
    # - Trigger: Called by workflow
    # - Upsert VAT company (buyer)
    # - Build RD address_raw
    # - Mark buyer_vat_info_status=true
    # - Mark buyer_vat_info_status=false
    # - Compare buyer address vs RD
    # - Merge: success payload + caller
    # - Branch: buyer address matches
    # - Mark buyer_address_status=true
    # - Mark buyer_address_status=false
    
    # BUT the connections block uses "VAT INFO1", "XML to JSON1", etc.
    # This implies the file `RDBuyerVATLookup.json` IS BROKEN or I am seeing a version of it that is completely messed up.
    # If I copy this file, I am copying a broken file.
    # However, the user said "Refactoring VAT Lookups" and "The user's goal is to refactor...".
    # Maybe the file works in n8n because n8n uses IDs? No, n8n JSON uses names for connections.
    # Wait, in recent n8n versions, they might use IDs?
    # The JSON shows `"id": "..."` for each node.
    # But the `connections` object keys are strings.
    # If I look at `ParallelSubWorkflow.json` (Step 498 - wait that was Vendor), I might see the same pattern.
    
    # Let's verify the content of `RDBuyerVATLookup.json` one more time.
    # I will read the `connections` block specifically to see if I missed something.
    # Or maybe I should just *trust* the node names I see and *rebuild* the connections based on those names in my script.
    # If the existing connections are broken, my script should fix them.
    # But if the existing connections use "VAT INFO1" and I don't have a node named "VAT INFO1", then the current file is indeed broken.
    
    # HYPOTHESIS: The file `RDBuyerVATLookup.json` on disk is NOT what is running or is a bad export.
    # OR, I am misreading the `connections` block.
    # Let's look at the `connections` block in Step 507 again.
    # Line 1023: `"VAT INFO1": { ... }`
    # Line 1104: `"When Executed by Another Workflow": { ... }`
    # Line 1125: `"Code in JavaScript": { ... }`
    
    # None of these node names exist in the `nodes` list I extracted.
    # This confirms the file is likely containing mismatching data.
    # This is a critical finding.
    
    # ACTION: I need to fix the connections to match the node names.
    # I will map the logical flow I see in the nodes to the connections.
    
    # Logical Flow in `RDBuyerVATLookup.json` (based on Node Names):
    # 1. Trigger: Called by workflow -> HTTP: RD VAT lookup (buyer)
    # 2. HTTP: RD VAT lookup (buyer) -> XML to JSON (RD)
    # 3. XML to JSON (RD) -> Normalize RD response (buyer)
    # 4. Normalize RD response (buyer) -> Upsert VAT company (buyer) AND Build RD address_raw?
    #    Wait, "Build RD address_raw" takes input from where?
    #    It probably takes input from "Trigger" (passed through) or "Normalize"?
    #    "Build RD address_raw" seems to process the *input* address (from PDF).
    #    So "Trigger" -> "Build RD address_raw".
    #    And "Trigger" -> "HTTP".
    
    #    "Normalize RD response (buyer)" -> "Merge: caller + RD response" (Input 2)
    #    "Trigger" (or Build RD address_raw?) -> "Merge: caller + RD response" (Input 1)
    
    #    "Merge: caller + RD response" -> "Branch: RD lookup failed"
    #    "Branch: RD lookup failed" (True) -> "Mark buyer_vat_info_status=false"
    #    "Branch: RD lookup failed" (False) -> "Branch: RD lookup success"
    
    #    "Branch: RD lookup success" (True) -> "Compare buyer address vs RD"
    #    "Compare buyer address vs RD" -> "Branch: buyer address matches"
    #    "Branch: buyer address matches" (True) -> "Mark buyer_address_status=true"
    #    "Branch: buyer address matches" (False) -> "Mark buyer_address_status=false"
    
    #    Also "Upsert VAT company (buyer)" needs to be connected.
    #    "Normalize RD response (buyer)" -> "Upsert VAT company (buyer)"
    
    #    And "Mark buyer_vat_info_status=true" needs to be connected.
    #    "Branch: buyer address matches" -> "Mark buyer_vat_info_status=true" (Parallel to address status update?)
    
    # This is a lot of guessing.
    # I should check `RDVendorVATLookup.json` again.
    # Step 498 shows `RDVendorVATLookup.json`.
    # Nodes: "Trigger...", "Merge...", "Branch...", "HTTP...", "XML...", "Normalize...", "Route VAT company upsert", "Build RD address_raw", "Upsert...", "Mark vendor...=true", "Mark vendor...=false".
    # This looks very similar.
    
    # I will write the script to REBUILD the connections entirely based on my understanding of the flow.
    # This is safer than trying to patch a potentially broken connections block.
    
    # Flow for `RDVATLookup.json`:
    # 1. "Trigger: Called by workflow" -> "HTTP: RD VAT lookup"
    # 2. "Trigger: Called by workflow" -> "Merge: caller + RD response" (Index 0)
    # 3. "HTTP: RD VAT lookup" -> "XML to JSON (RD)"
    # 4. "XML to JSON (RD)" -> "Normalize RD response"
    # 5. "Normalize RD response" -> "Upsert VAT company"
    # 6. "Normalize RD response" -> "Merge: caller + RD response" (Index 1)
    # 7. "Merge: caller + RD response" -> "Branch: RD lookup failed"
    # 8. "Branch: RD lookup failed" (True) -> "Route Type (Failure)"
    # 9. "Branch: RD lookup failed" (False) -> "Branch: RD lookup success"
    # 10. "Branch: RD lookup success" (True) -> "Route Type (Success)"
    # 11. "Route Type (Success)" (True/Buyer) -> "Compare buyer address vs RD"
    # 12. "Route Type (Success)" (False/Vendor) -> "Mark vendor_vat_id_info_status=true"
    # 13. "Route Type (Failure)" (True/Buyer) -> "Mark buyer_vat_info_status=false"
    # 14. "Route Type (Failure)" (False/Vendor) -> "Mark vendor_vat_id_info_status=false"
    # 15. "Compare buyer address vs RD" -> "Branch: buyer address matches"
    # 16. "Branch: buyer address matches" (True) -> "Mark buyer_address_status=true"
    # 17. "Branch: buyer address matches" (True) -> "Mark buyer_vat_info_status=true"
    # 18. "Branch: buyer address matches" (False) -> "Mark buyer_address_status=false"
    # 19. "Branch: buyer address matches" (False) -> "Mark buyer_vat_info_status=true" (Even if address mismatch, VAT info is found/valid?)
    #     In `RDBuyerVATLookup`, "Mark buyer_vat_info_status=true" is likely called if lookup success, regardless of address match.
    #     So "Branch: RD lookup success" -> "Mark buyer_vat_info_status=true" (via some path).
    #     Actually, `RDBuyerVATLookup` has "Mark buyer_vat_info_status=true".
    #     If I look at the nodes, "Mark buyer_vat_info_status=true" exists.
    #     It should probably be executed if "Branch: RD lookup success" is true.
    #     But in my flow above, I sent "Branch: RD lookup success" to "Route Type (Success)".
    #     For Buyer, it goes to "Compare buyer address vs RD".
    #     "Compare buyer address vs RD" outputs the comparison result.
    #     Then "Branch: buyer address matches".
    #     If I want to mark VAT info as true, I should do it in parallel or sequence.
    #     I'll connect "Branch: buyer address matches" (True AND False) to "Mark buyer_vat_info_status=true".
    #     So both outcomes of address check lead to updating `buyer_vat_info_status = true`.
    
    # One missing piece: "Build RD address_raw".
    # This node prepares the address string from the input (PDF data) for comparison.
    # It should be connected from "Trigger" and feed into "Compare buyer address vs RD"?
    # No, "Compare buyer address vs RD" reads `$input.all()`.
    # So "Build RD address_raw" just needs to run somewhere before "Compare".
    # I'll connect "Trigger" -> "Build RD address_raw" -> "Merge: caller + RD response" (Index 0)?
    # That way the merged data includes the built address.
    
    # Revised Connections Plan:
    # 1. "Trigger: Called by workflow" -> "HTTP: RD VAT lookup"
    # 2. "Trigger: Called by workflow" -> "Build RD address_raw"
    # 3. "Build RD address_raw" -> "Merge: caller + RD response" (Index 0)
    # 4. "HTTP: RD VAT lookup" -> "XML to JSON (RD)"
    # 5. "XML to JSON (RD)" -> "Normalize RD response"
    # 6. "Normalize RD response" -> "Upsert VAT company"
    # 7. "Normalize RD response" -> "Merge: caller + RD response" (Index 1)
    # ... rest as above.
    
    # This looks solid.

    with open('modify_workflow.py', 'w', encoding='utf-8') as f:
        f.write('''import json
import uuid

def create_uuid():
    return str(uuid.uuid4())

def main():
    file_path = r"C:\\Users\\thita\\docker\\workflows\\RDVATLookup.json"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    # 1. Update Workflow Name
    workflow['name'] = "RD VAT Lookup"

    # 2. Update Nodes
    # Rename and update parameters
    for node in workflow['nodes']:
        if node['name'] == "HTTP: RD VAT lookup (buyer)":
            node['name'] = "HTTP: RD VAT lookup"
            node['parameters']['body'] = node['parameters']['body'].replace("buyer_vat_id", "vat_id").replace("buyer_branch", "branch_id")
        
        elif node['name'] == "Upsert VAT company (buyer)":
            node['name'] = "Upsert VAT company"
            
        elif node['name'] == "Normalize RD response (buyer)":
            node['name'] = "Normalize RD response"

    # 3. Create New Nodes
    route_success_node = {
        "parameters": {
            "conditions": {
                "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict", "version": 2},
                "conditions": [{"id": create_uuid(), "leftValue": "={{ $json.type }}", "rightValue": "buyer", "operator": {"type": "string", "operation": "equals"}}],
                "combinator": "and"
            },
            "options": {}
        },
        "type": "n8n-nodes-base.if",
        "typeVersion": 2.2,
        "position": [-1200, -50],
        "id": create_uuid(),
        "name": "Route Type (Success)"
    }

    route_failure_node = {
        "parameters": {
            "conditions": {
                "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict", "version": 2},
                "conditions": [{"id": create_uuid(), "leftValue": "={{ $json.type }}", "rightValue": "buyer", "operator": {"type": "string", "operation": "equals"}}],
                "combinator": "and"
            },
            "options": {}
        },
        "type": "n8n-nodes-base.if",
        "typeVersion": 2.2,
        "position": [-800, 200],
        "id": create_uuid(),
        "name": "Route Type (Failure)"
    }

    vendor_success_node = {
        "parameters": {
            "operation": "update",
            "schema": {"__rl": True, "value": "public", "mode": "name"},
            "table": {"__rl": True, "value": "invoice_check_summary", "mode": "list", "cachedResultName": "invoice_check_summary"},
            "columns": {
                "mappingMode": "defineBelow",
                "value": {"vendor_vat_id_info_status": "={{ true }}", "invoice_number": "={{ $json.invoice_number }}"},
                "matchingColumns": ["invoice_number"]
            },
            "options": {}
        },
        "type": "n8n-nodes-base.postgres",
        "typeVersion": 2.6,
        "position": [-600, -400],
        "id": create_uuid(),
        "name": "Mark vendor_vat_id_info_status=true",
        "credentials": {"postgres": {"id": "59xvxQayjivgQ1fN", "name": "Postgres account 3"}}
    }

    vendor_failure_node = {
        "parameters": {
            "operation": "update",
            "schema": {"__rl": True, "value": "public", "mode": "name"},
            "table": {"__rl": True, "value": "invoice_check_summary", "mode": "list", "cachedResultName": "invoice_check_summary"},
            "columns": {
                "mappingMode": "defineBelow",
                "value": {"vendor_vat_id_info_status": "={{ false }}", "invoice_number": "={{ $json.invoice_number }}"},
                "matchingColumns": ["invoice_number"]
            },
            "options": {}
        },
        "type": "n8n-nodes-base.postgres",
        "typeVersion": 2.6,
        "position": [-600, 300],
        "id": create_uuid(),
        "name": "Mark vendor_vat_id_info_status=false",
        "credentials": {"postgres": {"id": "59xvxQayjivgQ1fN", "name": "Postgres account 3"}}
    }

    workflow['nodes'].extend([route_success_node, route_failure_node, vendor_success_node, vendor_failure_node])

    # 4. Rebuild Connections
    connections = {}

    def connect(source, target, source_index=0, target_index=0):
        if source not in connections:
            connections[source] = {"main": []}
        while len(connections[source]["main"]) <= source_index:
            connections[source]["main"].append([])
        connections[source]["main"][source_index].append({"node": target, "type": "main", "index": target_index})

    # Define the flow
    connect("Trigger: Called by workflow", "HTTP: RD VAT lookup")
    connect("Trigger: Called by workflow", "Build RD address_raw")
    
    connect("Build RD address_raw", "Merge: caller + RD response", 0, 0)
    
    connect("HTTP: RD VAT lookup", "XML to JSON (RD)")
    connect("XML to JSON (RD)", "Normalize RD response")
    
    connect("Normalize RD response", "Upsert VAT company")
    connect("Normalize RD response", "Merge: caller + RD response", 0, 1)
    
    connect("Merge: caller + RD response", "Branch: RD lookup failed")
    
    # Branch: RD lookup failed
    # True -> Failed
    connect("Branch: RD lookup failed", "Route Type (Failure)", 0, 0)
    # False -> Success (Note: 'If' node outputs [True, False]. 'success === false' means True is Failure)
    connect("Branch: RD lookup failed", "Branch: RD lookup success", 1, 0)
    
    # Branch: RD lookup success
    # True -> Success
    connect("Branch: RD lookup success", "Route Type (Success)", 0, 0)
    
    # Route Type (Success)
    # True (Buyer)
    connect("Route Type (Success)", "Compare buyer address vs RD", 0, 0)
    # False (Vendor)
    connect("Route Type (Success)", "Mark vendor_vat_id_info_status=true", 1, 0)
    
    # Route Type (Failure)
    # True (Buyer)
    connect("Route Type (Failure)", "Mark buyer_vat_info_status=false", 0, 0)
    # False (Vendor)
    connect("Route Type (Failure)", "Mark vendor_vat_id_info_status=false", 1, 0)
    
    # Compare buyer address vs RD
    connect("Compare buyer address vs RD", "Branch: buyer address matches")
    
    # Branch: buyer address matches
    # True -> Address Match
    connect("Branch: buyer address matches", "Mark buyer_address_status=true", 0, 0)
    connect("Branch: buyer address matches", "Mark buyer_vat_info_status=true", 0, 0)
    
    # False -> Address Mismatch
    connect("Branch: buyer address matches", "Mark buyer_address_status=false", 1, 0)
    connect("Branch: buyer address matches", "Mark buyer_vat_info_status=true", 1, 0)

    workflow['connections'] = connections

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=4)

if __name__ == "__main__":
    main()
''')
