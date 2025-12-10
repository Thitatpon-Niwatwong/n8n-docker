# n8n Docker Stack

Docker Compose stack for n8n with PostgreSQL, Grafana, Prometheus, pgAdmin, Loki/Promtail, and an optional account UI. Includes a helper script to import bundled workflows.

## Prerequisites
- Docker + Docker Compose
- PowerShell (for `setup.ps1`)
- Git (if cloning)

## Quick Start
1) Clone and enter the repo  
   ```bash
   git clone https://github.com/Thitatpon-Niwatwong/n8n-docker.git
   cd n8n-docker
   ```
2) Copy env template and edit values  
   ```bash
   cp .env.example .env
   ```
   Key settings: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `PGADMIN_DEFAULT_EMAIL`, `PGADMIN_DEFAULT_PASSWORD`, `TIMEZONE`.
3) Launch stack  
   ```bash
   docker-compose up -d
   ```
4) Import packaged workflows (asks for owner email if you want to attach `--userId`)  
   ```bash
   pwsh ./setup.ps1
   ```

## Services (default ports)
- n8n: http://localhost:5678
- Grafana: http://localhost:3000
- pgAdmin: http://localhost:5050
- Prometheus: http://localhost:9090
- Loki: runs headless; Promtail tails Docker logs
- account_ui: http://localhost:8080 (if built)

## Data & mounts
- `./n8n-data`, `./n8n-files` → n8n home and files
- `./postgres/data` → PostgreSQL data
- `./workflows` → JSON workflows imported by `setup.ps1`
- `./grafana`, `./prometheus`, `./loki`, `./promtail`, `./pgadmin` → respective configs/data

## Dev notes
- Workflow JSONs under `workflows/*.json` are normalized on commit via `scripts/n8n_cleaner.py` (Git filter `n8n-clean`). If you clone fresh, ensure the filter is configured:  
  `git config --local filter.n8n-clean.clean "python scripts/n8n_cleaner.py"`; `git config --local filter.n8n-clean.smudge cat`; `git config --local filter.n8n-clean.required true`.
