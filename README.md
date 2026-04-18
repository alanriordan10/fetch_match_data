# FetchMatchData - FastAPI

This repository exposes the Football-Data.org endpoints via a small FastAPI wrapper.

Requirements
- Python 3.10+
- Install dependencies:

```bash
pip install -r requirements.txt
```

Run

```bash
uvicorn app:app --reload
```

Endpoints
- GET /fixtures?grouped=true&max_gameweeks=3
- GET /results?grouped=true&max_gameweeks=3
- GET /standings
- GET /scores

Notes
- The app imports `fetch_data.py` and uses its existing functions and grouping helpers.
- Set your API key in `fetch_data.py` (currently hard-coded as API_KEY). Consider using env vars for production.

## Deploying to Azure App Service (Code Deploy)

These instructions deploy the app directly (no Docker). App Service will install dependencies from `requirements.txt` and run the startup command.

1. Create resources (example using Azure CLI):

```bash
az login
az group create -n fetchmatch-rg -l westeurope
az appservice plan create -n fetchmatch-plan -g fetchmatch-rg --is-linux --sku B1
az webapp create -g fetchmatch-rg -p fetchmatch-plan -n <YOUR_APP_NAME> --runtime "PYTHON:3.12"
```

2. Configure application settings (set your API key):

```bash
az webapp config appsettings set -g fetchmatch-rg -n <YOUR_APP_NAME> --settings \
  FOOTBALL_DATA_API_KEY="<YOUR_REAL_API_KEY>"
```

3. Set the startup command (Linux web app) to use Gunicorn + Uvicorn workers and bind to $PORT:

```bash
az webapp config set -g fetchmatch-rg -n <YOUR_APP_NAME> --startup-file "gunicorn -k uvicorn.workers.UvicornWorker app:app --bind 0.0.0.0:\$PORT --workers 2"
```

4. Deploy from GitHub (recommended):
- Add repository secret `AZURE_WEBAPP_PUBLISH_PROFILE` containing the publish profile xml for the target Web App (downloadable from Azure Portal -> Get publish profile).
- Add repository secret `AZURE_WEBAPP_NAME` with your app name.
- Push to `main` branch; GitHub Actions workflow in `.github/workflows/azure-appservice-deploy.yml` will deploy the app.

5. Health checks & logs:
- Enable Container or Web Server logging in Azure portal and use `az webapp log tail -n <YOUR_APP_NAME> -g fetchmatch-rg` to stream logs.
- Configure a health check path (e.g. `/health`) in the Azure portal under Monitoring -> Health check.

## Automated Azure setup script & GitHub Actions (Service Principal)

A helper script is provided to create the Azure resources and a service principal suitable for GitHub Actions.

Usage (local machine with Azure CLI + GitHub CLI optional):

```bash
# Make script executable
chmod +x scripts/azure_setup.sh

# Run script - it will create the resource group, app plan and webapp and print the service principal JSON
./scripts/azure_setup.sh fetchmatch-rg westeurope <YOUR_APP_NAME> fetchmatch-plan
```

The script will output a JSON blob. Add it to your GitHub repository secrets as `AZURE_CREDENTIALS`.

Required GitHub repository secrets for the workflow:
- AZURE_CREDENTIALS: service principal JSON produced by the script
- AZURE_WEBAPP_NAME: your web app name (string)
- AZURE_RESOURCE_GROUP: resource group name (string)

The provided GitHub Actions workflow (`.github/workflows/azure-appservice-deploy.yml`) will use these secrets to log in and deploy the code on pushes to `main`.
