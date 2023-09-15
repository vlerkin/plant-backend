from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from api.misc import router as misc_router
from api.plant import router as plant_router
from api.user import router as user_router

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.Configuration.cors_servers,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(misc_router)
app.include_router(plant_router)


# API
@app.get("/")
async def root():
    return {"message": "Hello World"}


