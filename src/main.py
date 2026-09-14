import subprocess, tempfile, resource, os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()
ROOT = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.get("/", include_in_schema=False)
def playground():
    return FileResponse(ROOT / "static" / "index.html")

class CheckRequest(BaseModel):
    code: str

def limit_resources():
    resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))

@app.post("/check")
def check(req: CheckRequest):
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(req.code)
        path = f.name
    try:
        result = subprocess.run(
            ["mypy", "--plugins", "your_plugin", "--no-incremental", path],
            capture_output=True, text=True, timeout=8,
            preexec_fn=limit_resources,
        )
        return {"stdout": result.stdout, "stderr": result.stderr}
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "type check timed out"}
    finally:
        os.unlink(path)
