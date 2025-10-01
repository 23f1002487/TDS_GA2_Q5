# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware  
# from pydantic import BaseModel
# import pandas as pd
# import traceback
# import os
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# app = FastAPI()

# # Request body schema
# class LatencyRequest(BaseModel):
#     regions: list[str]
#     threshold_ms: int


# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"], 
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# @app.get("/")
# def read_root():
#     return {"message": "Welcome to the API! Use the /latency endpoint with POST to get latency."}


# @app.post("/latency")
# def calculate_latency(request: LatencyRequest):
#     try:
#         file_path = os.path.join(BASE_DIR, "q-vercel-latency.json")
#         data = pd.read_json(file_path)
#         results = {}
#         for region in request.regions:
#             region_data = data[data["region"] == region]
#             if not region_data.empty:
#                 avg_latency = region_data["latency_ms"].mean()
#                 avg_uptime = region_data["uptime_pct"].mean()
#                 p95_latency = region_data["latency_ms"].quantile(0.95)
#                 breaches = int((region_data["latency_ms"] > request.threshold_ms).sum())
#                 results[region] = {
#                     "avg_latency": round(avg_latency, 2),
#                     "avg_uptime": round(avg_uptime, 2),
#                     "p95_latency": round(p95_latency, 2),
#                     "breaches": breaches,
#                 }
#             else:
#                 results[region] = {"error": "Region not found in data."}
#         return results
#     except Exception as e:
#         print("🔥 ERROR:", str(e))
#         print(traceback.format_exc())
#         return {"error": str(e)}


import http.server
import socketserver
import json
import pandas as pd

PORT = 8000

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/latency":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            request_data = json.loads(body.decode("utf-8"))

            # Load JSON file
            try:
                data = pd.read_json("q-vercel-latency.json")
            except FileNotFoundError:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "File not found"}).encode())
                return

            regions = request_data.get("regions", [])
            threshold = request_data.get("threshold_ms", 0)

            results = {}
            for region in regions:
                region_data = data[data["region"] == region]
                if not region_data.empty:
                    avg_latency = region_data["latency_ms"].mean()
                    avg_uptime = region_data["uptime_pct"].mean()
                    p95_latency = region_data["latency_ms"].quantile(0.95)
                    breaches = int((region_data["latency_ms"] > threshold).sum())

                    results[region] = {
                        "avg_latency": round(avg_latency, 2),
                        "avg_uptime": round(avg_uptime, 2),
                        "p95_latency": round(p95_latency, 2),
                        "breaches": breaches,
                    }
                else:
                    results[region] = {"error": "Region not found"}

            # Send response
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")  # basic CORS
            self.end_headers()
            self.wfile.write(json.dumps(results).encode())

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    print(f"Serving on port {PORT}")
    httpd.serve_forever()
