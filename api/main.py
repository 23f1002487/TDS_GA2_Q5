from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  
import numpy as np
import pandas as pd
import json


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],  
    allow_headers=["*"], 
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the API! Use the /latency endpoint with POST to get latency."}

@app.post("/latency")
def calculate_latency(request: json):
    # Load the data from the root directory
    with open('q-vercel-latency', 'r') as file:
        data = json.load(file)
    regions = request.arguments['regions']
    threshold = request.arguments['threshold_ms']
    results = {}
    for region in regions:
        if region in data:
            latencies = np.array(data[region])
            mean_latency = np.mean(latencies)
            std_latency = np.std(latencies)
            p95_latency = np.percentile(latencies, 95)
            breaches = np.sum(latencies > threshold)
            
            results[region] = {
                "avg_latency": mean_latency,
                "avg_uptime": std_latency,
                "p95_latency": p95_latency,
                "breaches": breaches
            }
        else:
            results[region] = {"error": "Region not found in data."}
    