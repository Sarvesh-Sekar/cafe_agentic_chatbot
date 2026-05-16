from fastmcp import FastMCP
from src.routers.mcp_router import router
from contextlib import asynccontextmanager
from src.migrations.create_tables import create_tables


@asynccontextmanager
async def lifespan(mcp:FastMCP):
    create_tables()
    yield


mcp = FastMCP("my-server",lifespan=lifespan)

# @mcp.exception_handler(CustomAppException)
# async def custom_app_exception_handler(request, exc: CustomAppException):
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={
#             "message": exc.message,
#             "status_code": exc.status_code,
#             "err_code": exc.err_code,
#         },
#     )

mcp.mount(router)



if __name__ == "__main__":

    
        # ══════════════════════════════════════════════════════════════
        # START AS HTTP SERVER (Streamable HTTP transport)
        # 
        # This starts a web server at http://localhost:8000/mcp
        # Any MCP client can connect to this URL over HTTP.
        #
        # Key difference from stdio:
        #   stdio  → mcp.run(transport="stdio")       → stdin/stdout
        #   http   → mcp.run(transport="streamable-http") → HTTP on port 8000
        # ══════════════════════════════════════════════════════════════
        print("🚀 Starting MCP Server (HTTP) at http://localhost:8000/mcp")
        print("   Press Ctrl+C to stop.\n")
        mcp.run(transport="streamable-http",host = "127.0.0.1",port = 8001)