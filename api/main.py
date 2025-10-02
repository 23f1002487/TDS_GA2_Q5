import os
import traceback

import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

"""API to calculate latency metrics per region for Vercel deployment."""

app = FastAPI()

# Request body schema
class LatencyRequest(BaseModel):
    """Pydantic model for latency request."""
    regions: list[str]
    threshold_ms: int

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

@app.get("/")
def read_root():
    """Return a welcome message for the API."""
    return {"message": "Welcome to the API! Use the /latency endpoint with POST to get latency."}

@app.post("/latency")
def calculate_latency(request: LatencyRequest):
    """Calculate per-region latency statistics based on the request."""
    try:
        file_path = os.path.join(BASE_DIR, "q-vercel-latency.json")
        data = pd.read_json(file_path)
        out = {"regions" : {}}
        temp = {}
        
        for region in request.regions:
            region_data = data[data["region"] == region]
            if not region_data.empty:
                avg_latency = region_data["latency_ms"].mean()
                avg_uptime = region_data["uptime_pct"].mean()
                p95_latency = region_data["latency_ms"].quantile(0.95)
                breaches = int((region_data["latency_ms"] > request.threshold_ms).sum())
                temp[region] = {
                    "avg_latency": round(avg_latency, 2),
                    "avg_uptime": round(avg_uptime, 2),
                    "p95_latency": round(p95_latency, 2),
                    "breaches": breaches,
                }
            else:
                temp[region] = {"error": "Region not found in data."}
        
        out["regions"] = temp
        
        return out
    
    except Exception as e:
        print("🔥 ERROR:", str(e))
        print(traceback.format_exc())
        return {"error": str(e)}