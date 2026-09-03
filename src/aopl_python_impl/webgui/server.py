# FastAPI entry for Cosmic Sheet — same AoP core, spreadsheet UI.
from __future__ import annotations

import argparse
import sys
import webbrowser
from pathlib import Path
from typing import Dict, Optional

STATIC_DIR = Path(__file__).resolve().parent / "static"


def _missing_web_extra() -> None:
    print(
        "Cosmic Sheet needs FastAPI and Uvicorn in this Python.\n"
        "  python -m pip install fastapi uvicorn\n"
        "That is enough if aop-calculator is already installed.\n"
        "\n"
        "pip install -e \".[web]\" rebuilds the Rust extension. On Windows that\n"
        "fails with 'used by another process' if Cosmic Scratchpad or web.py is\n"
        "still running — close those first, or skip -e and install the two\n"
        "packages above.",
        file=sys.stderr,
    )
    sys.exit(1)


try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles
    from pydantic import BaseModel, Field
except ImportError:
    app = None  # type: ignore[assignment]
else:
    from aopl_python_impl.webgui.sheet import evaluate_sheet

    class CellIn(BaseModel):
        expr: str = ""
        output_mode: str = "num"

    class EvaluateRequest(BaseModel):
        base: int = Field(default=10, ge=2)
        cells: Dict[str, CellIn] = Field(default_factory=dict)

    app = FastAPI(title="Cosmic Sheet", version="0.1.0")

    @app.post("/api/evaluate")
    def api_evaluate(payload: EvaluateRequest):
        cells = {
            addr: {"expr": cell.expr, "output_mode": cell.output_mode}
            for addr, cell in payload.cells.items()
        }
        try:
            return evaluate_sheet(payload.base, cells).to_dict()
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/health")
    def api_health():
        return {"ok": True, "engine": "aop"}

    @app.get("/")
    def index():
        return FileResponse(
            STATIC_DIR / "index.html",
            headers={"Cache-Control": "no-store"},
        )

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def main(argv: Optional[list[str]] = None) -> None:
    if app is None:
        _missing_web_extra()

    try:
        import uvicorn
    except ImportError:
        _missing_web_extra()

    parser = argparse.ArgumentParser(
        description="Cosmic Sheet — spreadsheet UI for the Alphabet of Powers engine."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args(argv)
    url = f"http://{args.host}:{args.port}"
    print(f"Cosmic Sheet -> {url}")
    if not args.no_browser:
        webbrowser.open(url)
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
