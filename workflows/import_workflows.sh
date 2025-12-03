#!/bin/sh

# Wait for n8n to be ready (optional, but good if running at startup)
# For manual run, we just iterate.

echo "Importing workflows from /workflows..."

for file in /workflows/*.json; do
  if [ -f "$file" ]; then
    echo "Importing $file..."
    n8n import:workflow --input "$file"
  fi
done

echo "Import complete."
