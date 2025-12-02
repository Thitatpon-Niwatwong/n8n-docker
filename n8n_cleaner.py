import sys
import json
import io

# Ensure stdin/stdout use utf-8
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def clean_n8n_json():
    try:
        # Read all input from stdin
        input_data = sys.stdin.read()
        
        if not input_data:
            return

        # Parse JSON
        data = json.loads(input_data)
        
        # Remove pinData if present
        if 'pinData' in data:
            del data['pinData']
            
        # Write back to stdout
        json.dump(data, sys.stdout, indent=2, ensure_ascii=False)
        
    except Exception as e:
        # If error (e.g. not valid JSON), output original content to be safe
        # or just fail. For git filter, outputting original is safer than empty.
        sys.stderr.write(f"Error cleaning JSON: {e}\n")
        sys.stdout.write(input_data)

if __name__ == "__main__":
    clean_n8n_json()
