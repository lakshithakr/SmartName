import sys
from fastapi import FastAPI

app = FastAPI()

@app.get("/check-venv/")
async def check_venv():
    return {"python_executable": sys.executable}

if __name__ == "__main__":
    import uvicorn
    # Listen on all interfaces so it is accessible remotely
    uvicorn.run(app, host="0.0.0.0", port=8000)