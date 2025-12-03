# n8n Docker Setup with Auto-Update System

This repository contains a Docker Compose setup for n8n, complete with PostgreSQL, Grafana, Prometheus, and a custom **Auto-Update System** for managing workflows remotely.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- [Git](https://git-scm.com/downloads)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/NovitechPee/bmu-n8n.git
    cd bmu-n8n
    ```

2.  **Configure Environment Variables:**
    Copy the example environment file and edit it:
    ```bash
    cp .env.example .env
    ```
    Open `.env` and configure your credentials:
    ```ini
    POSTGRES_USER=your_user
    POSTGRES_PASSWORD=your_password
    POSTGRES_DB=n8n
    PGADMIN_DEFAULT_EMAIL=admin@example.com
    PGADMIN_DEFAULT_PASSWORD=admin123
    TIMEZONE=Asia/Bangkok
    ```

3.  **Start the Services:**
    Run the following command to build and start the containers:
    ```bash
    docker-compose up -d
    ```
    
    To stop the services:
    ```bash
    docker-compose down
    ```

4.  **Initial Setup (Import Workflows):**
    After the containers are running, run the setup script to create your admin account and import the workflows:
    ```bash
    ./setup.sh
    ```
    *Follow the on-screen prompts to set up your email and password.*

## Accessing Services

- **n8n:** [http://localhost:5678](http://localhost:5678)
- **Grafana:** [http://localhost:3000](http://localhost:3000) (Default login: `admin` / `admin`)
- **PgAdmin:** [http://localhost:5050](http://localhost:5050)
- **Prometheus:** [http://localhost:9090](http://localhost:9090)

---

## 🔄 Auto-Update System Setup

This project includes a "System Updater" workflow that allows you to push workflow updates to clients remotely via GitHub.

### 1. Client-Side Setup (On the n8n instance)

1.  **Create an API Key:**
    - Go to n8n **Settings** > **Public API**.
    - Click **Create API Key**.
    - Copy the key.

2.  **Import the Updater Workflow:**
    - Import the file `workflows/System_Updater.json` into n8n.

3.  **Configure Credentials:**
    - Open the **System Updater** workflow.
    - Double-click the **Update Workflow API** node.
    - Under **Credentials**, create a new **Header Auth** credential.
    - **Name:** `X-N8N-API-KEY` (Must be exact).
    - **Value:** Paste your API Key.
    - **Auth Type:** Header.

4.  **Activate:**
    - Toggle the workflow to **Active**.
    - It is scheduled to run daily, or you can run it manually to test.

### 2. Developer-Side Usage (How to push updates)

1.  **Update a Workflow:**
    - Edit your workflow in n8n.
    - Export the workflow as a JSON file (e.g., `MyWorkflow.json`).
    - Overwrite the file in the `workflows/` folder of this repository.

2.  **Update the Manifest:**
    - Open `workflows/workflows_manifest.json`.
    - Ensure the `name` matches the workflow name in the client's n8n **exactly**.
    - Ensure the `url` points to the **Raw** GitHub URL of your new JSON file.
    ```json
    [
      {
        "name": "My Workflow Name",
        "url": "https://raw.githubusercontent.com/NovitechPee/bmu-n8n/develop/workflows/MyWorkflow.json"
      }
    ]
    ```

3.  **Push to GitHub:**
    ```bash
    git add .
    git commit -m "Update workflow version"
    git push
    ```

The client's n8n will automatically detect the change (based on the manifest) and update itself.
