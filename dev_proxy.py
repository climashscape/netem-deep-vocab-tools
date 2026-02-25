
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Allow all origins for dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/proxy/llm/chat/completions")
async def proxy_llm(request: Request):
    try:
        # Extract headers and body from incoming request
        headers = dict(request.headers)
        # Keep only essential headers for forwarding
        forward_headers = {
            "Authorization": headers.get("authorization", ""),
            "Content-Type": "application/json"
        }
        
        body = await request.json()
        
        # Priority: Custom header > .env > Default
        target_base_url = headers.get("x-target-base-url") or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        
        print(f"Proxy: Forwarding request to {target_base_url}/chat/completions")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{target_base_url}/chat/completions",
                    json=body,
                    headers=forward_headers,
                    timeout=60.0
                )
                print(f"Proxy: Received response {response.status_code} from {target_base_url}")
                
                return JSONResponse(
                    status_code=response.status_code,
                    content=response.json()
                )
            except httpx.RequestError as exc:
                print(f"Proxy: Request error occurred while requesting {exc.request.url!r}: {exc}")
                raise HTTPException(status_code=502, detail=f"Upstream request failed: {exc}")
            except Exception as exc:
                print(f"Proxy: Unexpected error: {exc}")
                raise HTTPException(status_code=500, detail=str(exc))
            
    except Exception as e:
        print(f"Proxy error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/image/{verb}")
async def get_verb_image(verb: str):
    # Normalize verb
    verb = verb.strip().lower()
    # Simple redirect to DiceBear (consistent with app.py's fallback)
    # Using the same URL pattern as app.py
    image_url = f"https://api.dicebear.com/9.x/icons/svg?seed={verb}"
    return RedirectResponse(image_url)

# Silence Vite HMR client 404s from Trae/VSCode injection
@app.get("/@vite/client", include_in_schema=False)
async def vite_client_silencer():
    return Response(content="console.log('Vite client silencer')", media_type="application/javascript")

# Serve static files from dist
# We mount dist to the root after the API routes
app.mount("/static", StaticFiles(directory="dist/static"), name="static")

@app.get("/{full_path:path}")
async def serve_index(full_path: str):
    # Try to serve files from dist first
    file_path = os.path.join("dist", full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    # Default to index.html for SPA-like behavior
    return FileResponse("dist/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
