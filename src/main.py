import os
import sys
import tempfile
from pathlib import Path
from threading import Lock

from .validate_plugin import validate_plugin

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
EXAMPLES_DIR = Path(__file__).parent / ".." / "examples"


@app.get("/examples")
def list_examples():
    examples = {}
    for example_dir in sorted(EXAMPLES_DIR.iterdir()):
        if not example_dir.is_dir():
            continue
        files = {}
        for filename in ("main.py", "plugin.py"):
            file_path = example_dir / filename
            if file_path.is_file():
                files[filename] = file_path.read_text()
        examples[example_dir.name] = files
    return examples


@app.get("/", include_in_schema=False)
def playground():
    return FileResponse(ROOT / "static" / "index.html")


class CheckRequest(BaseModel):
    code: str
    plugin_code: str | None = None
    no_plugin: bool = False


@app.post("/check")
def check(req: CheckRequest):
    if not req.no_plugin and req.plugin_code and req.plugin_code.strip():
        try:
            validate_plugin(req.plugin_code)
        except ValueError as e:
            return {"stdout": "", "stderr": str(e), "status": 1}

    temp_dir = None
    path_inserted = False

    with MYPY_LOCK:
        try:
            args = [
                "--no-incremental",
                "--command",
                req.code,
            ]

            if not req.no_plugin and req.plugin_code and req.plugin_code.strip():
                temp_dir = tempfile.mkdtemp(prefix="mypy_pg_")
                plugin_path = os.path.join(temp_dir, "user_plugin.py")
                with open(plugin_path, "w") as f:
                    f.write(req.plugin_code)

                config_path = os.path.join(temp_dir, "mypy.ini")
                with open(config_path, "w") as f:
                    f.write("[mypy]\n")
                    f.write("plugins = user_plugin\n")
                    f.write("show_error_codes = True\n")
                    f.write("show_column_numbers = True\n")

                args.extend(["--config-file", config_path])
                sys.path.insert(0, temp_dir)
                path_inserted = True

                if "user_plugin" in sys.modules:
                    del sys.modules["user_plugin"]
            else:
                args.extend(["--config-file", str(MYPY_CONFIG)])

            stdout, stderr, status = mypy_api.run(args)
        finally:
            if path_inserted:
                try:
                    sys.path.remove(temp_dir)
                except ValueError:
                    pass
            if temp_dir:
                try:
                    os.remove(os.path.join(temp_dir, "user_plugin.py"))
                    os.remove(os.path.join(temp_dir, "mypy.ini"))
                    os.rmdir(temp_dir)
                except OSError:
                    pass

    return {
        "stdout": stdout.replace("<string>", "main.py"),
        "stderr": stderr.replace("<string>", "main.py"),
        "status": status,
    }
