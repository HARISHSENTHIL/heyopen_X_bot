import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.poller import Poller

logging.basicConfig(level=logging.INFO)

poller = Poller()


@asynccontextmanager
async def lifespan(app: FastAPI):
    poller.start()
    yield
    poller.stop()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/status")
def status():
    with poller.status_lock:
        return dict(poller.status)
