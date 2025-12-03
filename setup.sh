#!/bin/bash

# Load environment variables if .env exists
if [ -f .env ]; then
  # Handle Windows line endings by stripping \r
  export $(grep -v '^#' .env | sed 's/\r$//' | xargs)
fi

# Configuration defaults (fallback to .env values or defaults)
CONTAINER_N8N="n8n"
CONTAINER_DB="postgres"
DB_USER=${POSTGRES_USER:-n8n}
DB_NAME=${POSTGRES_DB:-n8n}

echo "============================================="
echo "      n8n Standard Delivery Setup Script     "
echo "============================================="
echo "DEBUG: Configuration loaded."
echo "DEBUG: DB_USER=$DB_USER"
echo "DEBUG: DB_NAME=$DB_NAME"

# Helper function to get User ID safely via SQL file
get_user_id() {
    local email=$1
    echo "SELECT id FROM \"user\" WHERE email = '$email';" > check_user.sql
    docker cp check_user.sql $CONTAINER_DB://tmp/check_user.sql
    # Use //tmp to prevent Git Bash path conversion
    # Redirect stderr to null to hide "failed to get console mode"
    local id=$(docker exec $CONTAINER_DB psql -U $DB_USER -d $DB_NAME -t -f //tmp/check_user.sql 2>/dev/null | grep -oE '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}' | head -n 1)
    rm check_user.sql
    echo "$id"
}

# Helper function to list users for debug
debug_list_users() {
    echo "SELECT email FROM \"user\";" > list_users.sql
    docker cp list_users.sql $CONTAINER_DB://tmp/list_users.sql
    docker exec $CONTAINER_DB psql -U $DB_USER -d $DB_NAME -t -f //tmp/list_users.sql 2>/dev/null
    rm list_users.sql
}

# 1. Check if containers are running
if [ ! "$(docker ps -q -f name=$CONTAINER_N8N)" ]; then
    echo "Error: n8n container is not running. Please run 'docker-compose up -d' first."
    exit 1
fi

# 2. Ask for User Email
echo ""
echo "Please enter the email address for the n8n Owner account."
echo "If you haven't created an account yet, we can create one for you."
read -p "Email: " USER_EMAIL

if [ -z "$USER_EMAIL" ]; then
    echo "Error: Email cannot be empty."
    exit 1
fi

# 3. Check if user exists in DB
echo "Checking for user in database..."
USER_ID=$(get_user_id "$USER_EMAIL")

# Validate UUID format
if [[ ! "$USER_ID" =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ ]]; then
    USER_ID=""
fi

if [ -z "$USER_ID" ]; then
    echo "User '$USER_EMAIL' not found."
    read -p "Do you want to create a new Admin user with this email? (y/n): " CREATE_OPT
    if [ "$CREATE_OPT" == "y" ] || [ "$CREATE_OPT" == "Y" ]; then
        read -s -p "Enter Password: " USER_PASS
        echo ""
        
        # Create user via n8n CLI
        echo "Attempting to create user via CLI..."
        
        # Try modern command
        if ! docker exec -u node $CONTAINER_N8N n8n user:management:user:create --email "$USER_EMAIL" --password "$USER_PASS" --firstName "Admin" --lastName "User" --role global:owner >/dev/null 2>&1; then
            # Try legacy command
            if ! docker exec -u node $CONTAINER_N8N n8n user:create --email "$USER_EMAIL" --password "$USER_PASS" --firstName "Admin" --lastName "User" --role global:owner >/dev/null 2>&1; then
                echo "----------------------------------------------------------------"
                echo "Warning: Could not create user via CLI (Command not found)."
                echo "Please open http://localhost:5678 in your browser."
                echo "Create your owner account with email: $USER_EMAIL"
                echo "----------------------------------------------------------------"
                
                while true; do
                    read -p "Once you have created the account, press Enter to continue..."
                    
                    USER_ID=$(get_user_id "$USER_EMAIL")
                    
                    # Validate UUID format
                    if [[ "$USER_ID" =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ ]]; then
                        break
                    fi
                    
                    echo "Error: User '$USER_EMAIL' still not found in database."
                    echo "DEBUG: Current users in DB:"
                    debug_list_users
                    echo "----------------------------------------------------------------"
                    read -p "Did you create the account with '$USER_EMAIL'? (y to retry / n to abort): " RETRY
                    if [ "$RETRY" != "y" ] && [ "$RETRY" != "Y" ]; then
                        exit 1
                    fi
                done
            fi
        fi
        
        # If we didn't go into the manual loop, fetch ID again
        if [ -z "$USER_ID" ]; then
             USER_ID=$(get_user_id "$USER_EMAIL")
             # Validate UUID format
             if [[ ! "$USER_ID" =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ ]]; then
                USER_ID=""
             fi
        fi

    else
        echo "Aborting setup. Please create a user via the web UI first, then run this script again."
        exit 1
    fi
fi

if [ -z "$USER_ID" ]; then
    echo "Error: Could not find or create user. Please check logs."
    exit 1
fi

echo "Found User ID: $USER_ID"

# 4. Import Workflows
echo "Importing workflows from /workflows folder..."
docker exec -u node $CONTAINER_N8N n8n import:workflow --input /workflows --userId "$USER_ID"

echo "============================================="
echo "      Setup Complete! Workflows Imported.    "
echo "============================================="
echo "You can now log in at http://localhost:5678"
