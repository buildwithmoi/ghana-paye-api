import os

from fastapi import FastAPI, Query

from . import __version__
from .paye import calculate

app = FastAPI(
    title="Ghana PAYE API",
    version=__version__,
    description="Monthly PAYE and employee SSNIT for Ghana (Act 1178, from 1 Sep 2026).",
)


@app.get("/health")
def health() -> dict:
    # "commit" is baked into the Docker image at build time, so a deploy can check
    # that the server is really running the commit it just shipped.
    return {"status": "ok", "version": __version__, "commit": os.environ.get("GIT_SHA", "dev")}


@app.get("/paye")
def paye(
    basic: float = Query(..., ge=0, description="Monthly basic salary in GH₵"),
    allowances: float = Query(0, ge=0, description="Monthly taxable cash allowances in GH₵"),
) -> dict:
    return calculate(basic, allowances).as_dict()
