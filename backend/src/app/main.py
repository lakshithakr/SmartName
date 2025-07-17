import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.utils import gemma,gemma_post_processing,gemma_decsription,gemma_preprocess,RAG
app = FastAPI()

import time

start_all = time.time()


class Prompt(BaseModel):
    prompt: str

class DetailRequest(BaseModel):
    prompt: str
    domain_name: str

@app.post("/generate-domains/")
async def generate_domains_endpoint(prompt: Prompt):

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

    return {"domains": domain_names}

@app.post("/details/")
async def get_domain_details(request: DetailRequest):

    start_desc = time.time()
    dd, domain_name = gemma_decsription(request.domain_name, request.prompt)
    end_desc = time.time()
    print(f"[gemma_description] Time taken: {end_desc - start_desc:.2f} seconds")

    start_pre = time.time()
    dd = gemma_preprocess(dd, domain_name)
    end_pre = time.time()
    print(f"[gemma_preprocess] Time taken: {end_pre - start_pre:.2f} seconds")
    return dd

if __name__ == "__main__":
    import uvicorn
    # Listen on all interfaces so it is accessible remotely
    uvicorn.run(app, host="0.0.0.0", port=8000)