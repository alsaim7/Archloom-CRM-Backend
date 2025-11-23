import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import database
import models
from fastapi.middleware.cors import CORSMiddleware
from routers.registration import router as registration_router
from routers.auth import router as auth_router
from routers.users import router as users_router
from routers.cron_job import router as cron_router

# Environment detection
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # Default to development

# Set CORS origins based on environment
if ENVIRONMENT == "production":
    # In production, use both Front_URL and Domain_Front_URL
    Front_URL = os.getenv("Front_URL")
    Domain_Front_URL = os.getenv("Domain_Front_URL")
    if not Front_URL or not Domain_Front_URL:
        raise ValueError("Front_URL and Domain_Front_URL must be set in production environment")
    ALLOWED_ORIGINS = [Front_URL, Domain_Front_URL]
else:
    # In development, use Local_Front_URL
    Local_Front_URL = os.getenv("Local_Front_URL")  # Default fallback
    ALLOWED_ORIGINS = [Local_Front_URL]



app = FastAPI(
    title="Archloom Backend API",
    description="Backend API for Archloom",
    version="0.0.1"
)


# Create tables
def create_db_and_tables():
    models.SQLModel.metadata.create_all(database.engine)


create_db_and_tables()


# Root endpoint (no authentication required)
@app.get("/")
def root():
    return JSONResponse(content={"message": "Welcome to the Archloom Backend API. For documentation, please refer to /docs."})




app.include_router(registration_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(cron_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))  # Railway sets PORT env var
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)