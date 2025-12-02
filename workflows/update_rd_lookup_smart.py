import json
import uuid
import re

def create_uuid():
    return str(uuid.uuid4())

def main():
    rd_lookup_path = r"C:\Users\thita\docker\workflows\RDVATLookup.json"
    parallel_path = r"C:\Users\thita\docker\workflows\ParallelSubWorkflow.json"
    
    # 1. Update RDVATLookup.json to be smart
    with open(rd_lookup_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)
        
    # Generate new ID for the workflow
    new_workflow_id = "RDVATLookupConsolidated" # Custom ID or random
    workflow['id'] = new_workflow_id
    
    # Update HTTP Node
    for node in workflow['nodes']:
        if node['name'] == "HTTP: RD VAT lookup":
            # Use coalescing for vat_id and branch_id
            # Original replacement was: vat_id, branch_id
            # New: {{ $json.vat_id || $json.buyer_vat_id || $json.vendor_vat_id }}
            
            body = node['parameters']['body']
            # Regex to replace {{ $json.vat_id }} with smart check
            # Note: The previous script replaced buyer_vat_id with vat_id.
            
            # We need to be careful with the XML structure.
            # <vat:TIN>{{ $json.vat_id }}</vat:TIN>
            
            body = body.replace("{{ $json.vat_id }}", "{{ $json.vat_id || $json.buyer_vat_id || $json.vendor_vat_id }}")
            body = body.replace("{{ $json.branch_id }}", "{{ $json.branch_id || $json.buyer_branch || $json.vendor_branch }}")
            
            node['parameters']['body'] = body

        # Update Route Nodes to infer type
        if node['name'] in ["Route Type (Success)", "Route Type (Failure)"]:
            # Add OR condition: type == 'buyer' OR buyer_vat_id is not empty
            # Current condition: type == 'buyer'
            
            # We'll add a second condition group or just modify the existing one?
            # n8n 'If' node supports 'combinator'.
            # We want (type == 'buyer') OR ($json.buyer_vat_id exists)
            # But 'If' node usually does AND between conditions in a group, and OR between groups?
            # Actually, n8n If node structure:
            # conditions: { combinator: 'and', conditions: [...] }
            # To do OR, we need complex logic or multiple If nodes.
            # EASIER: Just check for 'buyer_vat_id' existence?
            # If we call it for Vendor, 'buyer_vat_id' should be undefined.
            # If we call it for Buyer, 'buyer_vat_id' should be defined.
            # So checking "buyer_vat_id is not empty" is sufficient for the legacy calls.
            # And checking "type == buyer" covers the new standardized calls.
            
            # Let's change the condition to:
            # String contains "buyer" in "type" OR "buyer_vat_id" is not empty.
            # n8n If node is limited.
            # Let's use a Code node to determine type before the If node?
            # Or just check: {{$json.type === 'buyer' || $json.buyer_vat_id !== undefined}}
            # We can use an expression in the Boolean check!
            
            # Change operator to 'boolean' and value to expression.
            
            node['parameters']['conditions'] = {
                "options": {
                    "caseSensitive": True,
                    "leftValue": "",
                    "typeValidation": "strict",
                    "version": 2
                },
                "conditions": [
                    {
                        "id": create_uuid(),
                        "leftValue": "={{ $json.type === 'buyer' || $json.buyer_vat_id !== undefined }}",
                        "rightValue": "",
                        "operator": {
                            "type": "boolean",
                            "operation": "true",
                            "singleValue": True
                        }
                    }
                ],
                "combinator": "and"
            }

    with open(rd_lookup_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=4)
        
    # 2. Update ParallelSubWorkflow.json
    with open(parallel_path, 'r', encoding='utf-8') as f:
        parallel = json.load(f)
        
    # Find Execute Workflow nodes and update ID
    # Old IDs: rSF9qHXCIEXaHRo0 (Buyer), pEZ6RDmpdq9p5KH2 (Vendor)
    
    updated_count = 0
    for node in parallel['nodes']:
        if node['type'] == "n8n-nodes-base.executeWorkflow":
            wf_id_param = node['parameters'].get('workflowId')
            if wf_id_param:
                # Handle object or string
                current_id = wf_id_param.get('value') if isinstance(wf_id_param, dict) else wf_id_param
                
                if current_id in ["rSF9qHXCIEXaHRo0", "pEZ6RDmpdq9p5KH2"]:
                    if isinstance(wf_id_param, dict):
                        node['parameters']['workflowId']['value'] = new_workflow_id
                    else:
                        node['parameters']['workflowId'] = new_workflow_id
                    updated_count += 1
                    
    print(f"Updated {updated_count} nodes in ParallelSubWorkflow.json")

    with open(parallel_path, 'w', encoding='utf-8') as f:
        json.dump(parallel, f, indent=4)

if __name__ == "__main__":
    main()
