# Website
 https://github.com/sethjuarez/sustineo
 
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


# backend
- from sustineo root directory
- `python -m uvicorn api.main:app --reload`

# frontend
- from sustineo root directory
- `cd web`
- `npm run dev`


# Notes

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