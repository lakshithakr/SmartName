import logging
import sys
import time
import uuid
from pythonjsonlogger import jsonlogger

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from pymongo import MongoClient
from typing import Optional
from datetime import datetime
import pytz
import os
import json

from src.utils import (
    gemma, gemma_post_processing, gemma_decsription, gemma_preprocess,
    RAG, is_domain_names_available, extend_domains, get_domain_scores, generate_domain_suggestions,extend_domain_list_shorting,remove_case_duplicates
)

# ---- Logging config (JSON to stdout) ----
logger = logging.getLogger()
logger.handlers = []  # avoid duplicate handlers in reload
handler = logging.StreamHandler(sys.stdout)
formatter = jsonlogger.JsonFormatter()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

app = FastAPI()

origins = [
    "https://smartname.lk",
    "https://smartnames.lk"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ---- Request ID middleware for correlation ----
@app.middleware("http")
async def add_request_id_logging(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start = time.time()

    # Basic request log
    logger.info({
        "event": "http.request",
        "method": request.method,
        "path": request.url.path,
        "request_id": request_id,
        "client": request.client.host if request.client else None
    })

    response = await call_next(request)

    duration_ms = int((time.time() - start) * 1000)
    logger.info({
        "event": "http.response",
        "status_code": response.status_code,
        "path": request.url.path,
        "duration_ms": duration_ms,
        "request_id": request_id
    })
    # Propagate request ID back to client
    response.headers["X-Request-ID"] = request_id
    return response

# ---- Mongo ----
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongodb:27017")  # use service DNS in compose network
client = MongoClient(MONGO_URI)
db = client["smartname"]
feedback_collection = db["feedbacks"]
search_log_collection = db["logged-data"]
#descriptions_collection = db["descriptions"]

class Prompt(BaseModel):
    prompt: str

class DetailRequest(BaseModel):
    prompt: str
    domain_name: str

class Feedback(BaseModel):
    rating: int
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    comment: str

class DescriptionEntry(BaseModel):
    prompt: str
    domain_name: str
    description: dict
    timestamp: str
    ip_address: Optional[str] = None

@app.post("/generate-extra-domains/")
async def generate_extra_domains(prompt: Prompt, request: Request):
    logger.info({"event": "generate_extra_domains.start"})
    domains = generate_domain_suggestions(prompt.prompt)
    domains = get_domain_scores(domains)
    logger.info({"event": "generate_extra_domains.done", "prompt": prompt.prompt,"count": len(domains)})
    return {"domains": domains}

@app.post("/submit-feedback/")
def submit_feedback(feedback: Feedback, request: Request):
    sri_lanka_tz = pytz.timezone("Asia/Colombo")
    doc = feedback.dict()
    doc["submitted_at"] = datetime.now(sri_lanka_tz).strftime("%Y-%m-%d %H:%M:%S")
    feedback_collection.insert_one(doc)
    logger.info({"event": "feedback.submitted", "rating": feedback.rating,"name":feedback.name,"email": feedback.email})
    return {"message": "Feedback saved successfully"}

@app.post("/generate-domains/")
async def generate_domains_endpoint(prompt: Prompt, request: Request):
    sri_lanka_tz = pytz.timezone("Asia/Colombo")
    t0 = time.time()

    # Client IP (respect proxy)
    x_forwarded_for = request.headers.get('X-Forwarded-For')
    ip_address = x_forwarded_for.split(",")[0].strip() if x_forwarded_for else (request.client.host if request.client else None)

    logger.info({"event": "domains.generate.start", "ip": ip_address})

    # RAG
    t_rag0 = time.time()
    samples = RAG(prompt.prompt)
    t_rag1 = time.time()
    logger.info({"event": "rag.timing", "ms": int((t_rag1 - t_rag0) * 1000)})

    # LLM generate
    t_llm0 = time.time()
    output = gemma(prompt.prompt, samples)
    t_llm1 = time.time()
    logger.info({"event": "llm.timing", "ms": int((t_llm1 - t_llm0) * 1000)})

    # Post-process
    domain_names = gemma_post_processing(output)
    if 0 < len(domain_names) < 4:
        domain_names = extend_domains(domain_names)
    #domain_names= extend_domain_list_shorting(domain_names)
    domain_names = is_domain_names_available(domain_names)
    domain_names = get_domain_scores(domain_names)

    timestamp = datetime.now(sri_lanka_tz).strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "search_query": prompt.prompt,
        "domain_recommendations": domain_names,
        "ip_address": ip_address,
        "timestamp": timestamp
    }
    search_log_collection.insert_one(log_entry)

    logger.info(json.dumps({
        "event": "domains.generate.done",
        "prompt": prompt.prompt,
        "recommendations": domain_names,
        "ip_address": ip_address,
        "duration_ms": int((time.time() - t0) * 1000)
    }))

    return {"domains": domain_names}

@app.post("/details/")
async def get_domain_details(request_body: DetailRequest, request: Request):
    x_forwarded_for = request.headers.get('X-Forwarded-For')
    ip_address = x_forwarded_for.split(",")[0].strip() if x_forwarded_for else (request.client.host if request.client else None)
    sri_lanka_tz = pytz.timezone("Asia/Colombo")

    logger.info({"event": "details.generate.start", "domain": request_body.domain_name})

    t0 = time.time()
    dd_text, domain_name = gemma_decsription(request_body.domain_name, request_body.prompt)
    t1 = time.time()
    dd = gemma_preprocess(dd_text, domain_name)
    t2 = time.time()

    # descriptions_collection.insert_one({
    #     "prompt": request_body.prompt,
    #     "domain_name": request_body.domain_name,
    #     "description": dd,
    #     "timestamp": datetime.now(sri_lanka_tz).strftime("%Y-%m-%d %H:%M:%S"),
    #     "ip_address": ip_address
    # })

    logger.info({
        "event": "details.generate.done",
        "prompt":request_body.prompt,
        "description":dd,
        "ip_address": ip_address,
        "timing_ms": {"llm": int((t1 - t0) * 1000), "preprocess": int((t2 - t1) * 1000)}
    })
    return dd

if __name__ == "__main__":
    import uvicorn
    # Enable uvicorn access logs (already JSON via our root handler)
    uvicorn.run(app, host="0.0.0.0", port=8000, access_log=True)
