# Website
 https://github.com/sethjuarez/sustineo
-

 # Video
 https://www.youtube.com/watch?v=WH9iBu9hT4E
 Evolution Diagram: 5:28
 Differences diagram: 6:43
 Agentic development diagram: 8:13
 Usages: 11:51-17:00
 AI Agent Service: 17:10
 AI Agent Service Archiectures/Configurations: 20:02
 Amanda Demo: 23:40
 Evaluators: 32:30
 43:04

# Arch
https://github.com/sethjuarez/sustineo/blob/copilot/fix-36/readme.md

# Setup
https://github.com/sethjuarez/sustineo/blob/copilot/fix-37/SETUP.md


# To Run
## backend (api)
- from sustineo root directory
- `python -m uvicorn api.main:app --reload`

## frontend (web)
- from sustineo root directory
- `cd web`
- `npm run dev`

# Notes

## Setup dotenv file
Sample dotenv going in the root of sustineo
```
# Azure OpenAI for Voice

AZURE_VOICE_ENDPOINT=https://ai-mwise9711ai638745858620.openai.azure.com/openai/realtime?api-version=2024-10-01-preview&deployment=gpt-4o-realtime-preview
AZURE_VOICE_KEY=.... random letters ...


# Azure OpenAI for Image Generation
AZURE_IMAGE_ENDPOINT=https://wiseaifoundry.openai.azure.com/
AZURE_IMAGE_API_KEY=.... random letters ...

# Azure Storage
SUSTINEO_STORAGE=https://azfmagstorage.blob.core.windows.net/

# Azure Cosmos DB
# AccountEndpoint=https://azfcosmosdb.documents.azure.com:443/;AccountKey=.... random letters ending in ==semicolon
COSMOSDB_CONNECTION="AccountEndpoint=https://azfcosmosdb.documents.azure.com:443/;AccountKey=.... random letters ending in ==semicolon"

FOUNDRY_CONNECTION=eastus2.api.azureml.ms;57b15bf0-e8dd-458a-9156-0694edd7ad4e;rg-mwise-6144_ai;mwise-0178

# Optional: Local tracing
LOCAL_TRACING_ENABLED=true
```

## Installing and initializing backend (api)
- `cd api`
- `py -m venv .venv` (used python 3.13)
- `.venv\Scripts\activate.bat`
- `pip install -r requirements.txt`
- `cd ..`
- setup a cosmos db (documentdb) in your sub
   - you will need to set the key into the .env file
- `az cli login` to the right subscription (the one with the cosmosdb)
   - You have to make sure the cosmosdb can be reached (make it public)
   - everyday this setting will be turned off
   - It will also oddly wipe your prompt configuration data
- `python -m uvicorn api.main:app --reload`
- Open http://127.0.0.1:8000/api/configuration to load cosmos prompt configuration data

## Installing web
- probably want to install nvm or nvm-windows (github) for node version management
- npm is for pakcage management, not the same
- `node -v` to get version, needs version 20 or better
- `nvm list`
- `nvm install 22.14.0`
- `npm install` - npm and nvm are different - npm to install needed packages
- `npm run dev` - and then click on link  `http://localhost:5173/` to run

## Debug
- `cd api`
- `.venv\Scripts\activate.bat`
- `cd ..`
- `code .`
- Debug then Select FastAPI debug configuration
- Have to make cosmosdb instance public (or something)
- Have to install configurations with `http://127.0.0.1:8000/api/configuration`

## Voice Model Deployment
- The code has gpt-40-realtime-preview, but I couldn't get it to the model to load (diverse 404, and 401 errors)
- I found sample code for gpt-4o-mini-realtime-preview and tried that sample
- In the case of gpt-40-mini-preview it seems to have mapped my deployment to one in another project in my subscription, although neither of these seem to be hub projects. When I used the endpoints and keys from that project I got it to work.
- I had to use 2025-04-01-preview for this to work.
- The connections string copy in the AI Foundry UI never worked for me, that wasted a lot of time.
- now have it working on gpt-4o-realtime-preview

## Cosmos DB
- the LoadEnv is placed in main.py after cosmos has already been imported, so it doesn't get the env var. I moved it back towards the top (got parse error message).
- I created a new cosmosdb for this, since I was testing from outside corpnet, I had to implement public access
  - `Message: Request originated from IP 157.58.213.226 through public internet. This is blocked by your Cosmos DB account firewall settings. More info: https://aka.ms/cosmosdb-tsg-forbidden`
  - StackOverflow: https://stackoverflow.com/questions/69120660/setting-offer-throughput-or-autopilot-on-container-is-not-supported-for-serverle
- I got another warning about setting rate limits on serverless dbs, I had to comment out a parameter to work around this. (common.py line 127, `#        offer_throughput=400,`)
   - `Message: Setting offer throughput or autopilot on container is not supported for serverless accounts.`