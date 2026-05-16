from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.routers.router import router
from src.utils.custom_app_exception import CustomAppException





app = FastAPI(
    title="Bean & Brew Chatbot",
    description="AI-powered coffee shop chatbot using AWS Bedrock",
    version="1.0.0"
)

app.include_router(router)


@app.exception_handler(CustomAppException)
async def custom_app_exception_handler(request, exc: CustomAppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.message,
            "status_code": exc.status_code,
            "err_code": exc.err_code,
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
