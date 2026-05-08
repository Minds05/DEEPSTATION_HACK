from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from routers import agent, logistics

app = FastAPI(title="Sentinel Library Intelligence System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent.router, prefix="/agent", tags=["agent"])
app.include_router(logistics.router, prefix="/logistics", tags=["logistics"])

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Sentinel Library Intelligence System Backend Running"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
