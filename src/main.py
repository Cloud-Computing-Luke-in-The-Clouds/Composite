import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# from src.composite.router import router
# from src.researcher.router import router  # use this for running researcher service locally
from src.testcomposite.router import router
from fastapi_pagination import add_pagination
from src.middleware_logging import log_requests
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(BaseHTTPMiddleware, dispatch=log_requests)


@app.get("/")
async def root():
    return {"message": "Hello World"}

app.include_router(router)
add_pagination(app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
