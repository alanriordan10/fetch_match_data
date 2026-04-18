try:
    from fastapi import FastAPI, HTTPException, Query
    from fastapi.responses import JSONResponse
except Exception:
    # Fallback stubs for environments where FastAPI is not installed (helps static checks)
    from typing import Any

    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: Any = None):
            super().__init__(detail)
            self.status_code = status_code
            self.detail = detail

    def Query(default: Any = None, **kwargs):
        return default

    class FastAPI:
        def __init__(self, *args, **kwargs):
            pass

        def get(self, *args, **kwargs):
            def decorator(func):
                return func

            return decorator

    class JSONResponse(dict):
        def __init__(self, content):
            super().__init__(content)

from typing import Optional

import fetch_data

app = FastAPI(title="FetchMatchData API", version="0.1")


def _limit_groups(groups: dict, max_groups: Optional[int]) -> dict:
    if max_groups is None:
        return groups
    keys = list(groups.keys())[:max_groups]
    return {k: groups[k] for k in keys}


@app.get("/", tags=["meta"])
async def root():
    return {
        "service": "FetchMatchData API",
        "endpoints": {
            "/fixtures": "GET fixtures (query: grouped=true/false, max_gameweeks=int)",
            "/results": "GET results (query: grouped=true/false, max_gameweeks=int)",
            "/standings": "GET current standings",
            "/scores": "GET live scores",
        },
    }


@app.get("/health", tags=["meta"])
async def health():
    # simple liveness/health endpoint
    return {"status": "ok"}


@app.get("/fixtures", tags=["fixtures"])
async def api_fixtures(grouped: bool = Query(True), max_gameweeks: Optional[int] = Query(None)):
    data = fetch_data.get_fixtures()
    if not data:
        raise HTTPException(status_code=503, detail="Unable to fetch fixtures")

    if grouped:
        grouped_data = fetch_data.group_fixtures_by_gameweek(data)
        limited = _limit_groups(grouped_data, max_gameweeks)
        return JSONResponse(content={"grouped": limited})

    return JSONResponse(content=data)


@app.get("/results", tags=["results"])
async def api_results(grouped: bool = Query(True), max_gameweeks: Optional[int] = Query(None)):
    data = fetch_data.get_results()
    if not data:
        raise HTTPException(status_code=503, detail="Unable to fetch results")

    if grouped:
        grouped_data = fetch_data.group_results_by_gameweek(data)
        limited = _limit_groups(grouped_data, max_gameweeks)
        return JSONResponse(content={"grouped": limited})

    return JSONResponse(content=data)


@app.get("/standings", tags=["standings"])
async def api_standings():
    data = fetch_data.get_standings()
    if not data:
        raise HTTPException(status_code=503, detail="Unable to fetch standings")
    return JSONResponse(content=data)


@app.get("/scores", tags=["scores"])
async def api_scores():
    data = fetch_data.get_scores()
    if not data:
        return JSONResponse(content={"matches": []})
    return JSONResponse(content=data)


@app.get("/ready", tags=["meta"])
async def ready():
    # readiness probe: basic internal checks (do not call slow external APIs)
    # Here we just verify that module import succeeded and return ok
    return {"status": "ready"}


@app.get("/metrics", tags=["meta"])
async def metrics():
    # simple metrics stub - extend with Prometheus client if needed
    return {
        "uptime_seconds": 0,
        "requests_total": 0,
    }
