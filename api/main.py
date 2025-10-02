from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  
from pydantic import BaseModel
import pandas as pd
import traceback
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI()

# Request body schema
class LatencyRequest(BaseModel):
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
    return {"message": "Welcome to the API! Use the /latency endpoint with POST to get latency."}


@app.post("/latency")
def calculate_latency(request: LatencyRequest):
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

# import json
# import os
# import pandas as pd
# from http.server import BaseHTTPRequestHandler

# # Path to your JSON file
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# JSON_FILE = os.path.join(BASE_DIR, "q-vercel-latency.json")

# class handler(BaseHTTPRequestHandler):
#     def _set_headers(self):
#         self.send_response(200)
#         self.send_header("Content-type", "application/json")
#         self.send_header("Access-Control-Allow-Origin", "*")  # CORS
#         self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
#         self.send_header("Access-Control-Allow-Headers", "Content-Type")
#         self.end_headers()

#     def do_OPTIONS(self):
#         """Handle CORS preflight"""
#         self._set_headers()

#     def do_GET(self):
#         self._set_headers()
#         self.wfile.write(json.dumps({"message": "Hello! Use POST /latency"}).encode("utf-8"))

#     def do_POST(self):
#         if self.path != "/latency":
#             self.send_response(404)
#             self.end_headers()
#             self.wfile.write(b"Not Found")
#             return

#         content_length = int(self.headers.get("Content-Length", 0))
#         body = self.rfile.read(content_length)
#         request_data = json.loads(body.decode("utf-8"))

#         # Load JSON
#         data = pd.read_json(JSON_FILE)

#         regions = request_data.get("regions", [])
#         threshold = request_data.get("threshold_ms", 0)

#         results = {}
#         for region in regions:
#             region_data = data[data["region"] == region]
#             if not region_data.empty:
#                 avg_latency = region_data["latency_ms"].mean()
#                 avg_uptime = region_data["uptime_pct"].mean()
#                 p95_latency = region_data["latency_ms"].quantile(0.95)
#                 breaches = int((region_data["latency_ms"] > threshold).sum())

#                 results[region] = {
#                     "avg_latency": round(avg_latency, 2),
#                     "avg_uptime": round(avg_uptime, 2),
#                     "p95_latency": round(p95_latency, 2),
#                     "breaches": breaches,
#                 }
#             else:
#                 results[region] = {"error": "Region not found"}

#         self._set_headers()
#         self.wfile.write(json.dumps(results).encode("utf-8"))
