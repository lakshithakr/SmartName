import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from pymongo import MongoClient
from fastapi import Request
import pytz
from typing import Optional
from datetime import datetime
from src.utils import gemma,gemma_post_processing,gemma_decsription,gemma_preprocess,RAG, is_domain_names_available
app = FastAPI()


origins = [
    #"http://localhost",
    #"http://127.0.0.1",
    #"http://frontend",  # Docker service name
    #"http://173.208.232.91",
    #"http://173.208.232.91:3000",  # Add this!
    #"http://localhost:3000",        # If testing locally
    "https://smartname.lk",
    #"http://localhost:80",          # If using Nginx
    #"http://0.0.0.0"                # Optional
    ] # Adjust if your frontend is hosted elsewhere

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

MONGO_URI = "mongodb://173.208.232.91:27018"
client = MongoClient(MONGO_URI)
db = client["smartname"]
feedback_collection = db["feedbacks"]
search_log_collection = db["logged-data"]
descriptions_collection = db["descriptions"]

import time

start_all = time.time()


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

@app.post("/submit-feedback/")
def submit_feedback(feedback: Feedback):
    feedback_data = feedback.dict()
    # Define Sri Lankan timezone
    sri_lanka_tz = pytz.timezone("Asia/Colombo")
    # Get current time in Sri Lankan timezone
    feedback_data["submitted_at"] = datetime.now(sri_lanka_tz).strftime("%Y-%m-%d %H:%M:%S")
    feedback_collection.insert_one(feedback_data)
    return {"message": "Feedback saved successfully"}

@app.post("/generate-domains/")
async def generate_domains_endpoint(prompt: Prompt,request: Request):

    start_rag = time.time()
    samples = RAG(prompt.prompt)
    end_rag = time.time()
    print(f"[RAG] Time taken: {end_rag - start_rag:.2f} seconds")

    print(samples)

    start_gemma = time.time()
    output = gemma(prompt.prompt, samples)
    end_gemma = time.time()
    print(f"[Gemma] Time taken: {end_gemma - start_gemma:.2f} seconds")


    domain_names=gemma_post_processing(output)   # for  Gemma
    domain_names=is_domain_names_available(domain_names)

    sri_lanka_tz = pytz.timezone("Asia/Colombo")
    timestamp = datetime.now(sri_lanka_tz).strftime("%Y-%m-%d %H:%M:%S")

    x_forwarded_for = request.headers.get('X-Forwarded-For')
    if x_forwarded_for:
        # X-Forwarded-For can contain multiple IPs, client is the first one
        ip_address = x_forwarded_for.split(",")[0].strip()
    else:
        ip_address = request.client.host
    #ip_address = request.client.host

    log_entry = {
        "search_query": prompt.prompt,
        "domain_recommendations": domain_names,
        "ip_address": ip_address,
        "timestamp": timestamp
    }
    search_log_collection.insert_one(log_entry)
    return {"domains": domain_names}

@app.post("/details/")
async def get_domain_details(request: DetailRequest,fastapi_request: Request):

    start_desc = time.time()
    dd, domain_name = gemma_decsription(request.domain_name, request.prompt)
    end_desc = time.time()
    print(f"[gemma_description] Time taken: {end_desc - start_desc:.2f} seconds")

    start_pre = time.time()
    dd = gemma_preprocess(dd, domain_name)
    end_pre = time.time()
    print(f"[gemma_preprocess] Time taken: {end_pre - start_pre:.2f} seconds")
        # Get IP
    x_forwarded_for = fastapi_request.headers.get('X-Forwarded-For')
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(",")[0].strip()
    else:
        ip_address = fastapi_request.client.host

    # Prepare data
    sri_lanka_tz = pytz.timezone("Asia/Colombo")
    description_entry = DescriptionEntry(
        prompt=request.prompt,
        domain_name=request.domain_name,
        description=dd,
        timestamp=datetime.now(sri_lanka_tz).strftime("%Y-%m-%d %H:%M:%S"),
        ip_address=ip_address
    )

    # Save to MongoDB
    descriptions_collection.insert_one(description_entry.dict())
    return dd

if __name__ == "__main__":
    import uvicorn
    # Listen on all interfaces so it is accessible remotely
    uvicorn.run(app, host="0.0.0.0", port=8000)