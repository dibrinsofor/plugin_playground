from pathlib import Path
from threading import Lock

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from mypy import api as mypy_api
from pydantic import BaseModel

app = FastAPI()
ROOT = Path(__file__).resolve().parent.parent
MYPY_CONFIG = ROOT / "mypy.ini"
MYPY_LOCK = Lock()
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.get("/", include_in_schema=False)
def playground():
    return FileResponse(ROOT / "static" / "index.html")

class CheckRequest(BaseModel):
    code: str

@app.post("/check")
def check(req: CheckRequest):
    with MYPY_LOCK:
        stdout, stderr, status = mypy_api.run(
            [
                "--config-file",
                str(MYPY_CONFIG),
                "--no-incremental",
                "--command",
                req.code,
            ]
        )

    return {
        "stdout": stdout.replace("<string>", "main.py"),
        "stderr": stderr.replace("<string>", "main.py"),
        "status": status,
    }
