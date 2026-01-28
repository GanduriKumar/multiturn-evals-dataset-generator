from fastapi import FastAPI

app = FastAPI(title="Eval Dataset Generator")


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}
