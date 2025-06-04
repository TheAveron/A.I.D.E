from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import offer

from .api import auth, faction, user
from .database import Base, engine

app = FastAPI(title="A.I.D.E Backend")

Base.metadata.create_all(bind=engine)  # Create database tables

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(user.router)
app.include_router(faction.router)
app.include_router(auth.router)
app.include_router(offer.router)


@app.get("/")
def root():
    return {"message": "A.I.D.E backend is running"}
