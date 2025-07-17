import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.utils import gemma,gemma_post_processing,gemma_decsription,gemma_preprocess
app = FastAPI()



class Prompt(BaseModel):
    prompt: str

class DetailRequest(BaseModel):
    prompt: str
    domain_name: str

@app.post("/generate-domains/")
async def generate_domains_endpoint(prompt: Prompt):

    samples='morabike ,greenpedal,ecozoom ,commutiva  ,pedalwave  ,cyclovia  ,ridewell  ,urbicycle  ,biketraq  ,moracycle'
    output=gemma(prompt.prompt,samples)
    domain_names=gemma_post_processing(output)   # for  Gemma

    return {"domains": domain_names}

@app.post("/details/")
async def get_domain_details(request: DetailRequest):

    dd,domain_name=gemma_decsription(request.domain_name,request.prompt)
    dd=gemma_preprocess(dd,domain_name) # for gemma
    return dd

if __name__ == "__main__":
    import uvicorn
    # Listen on all interfaces so it is accessible remotely
    uvicorn.run(app, host="0.0.0.0", port=8000)