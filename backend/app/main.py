from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.project_detection import router as project_detection_router
from app.routes.project_normalization import router as project_normalization_router
from app.routes.project_migration_planner import router as project_migration_planner_router

app = FastAPI(title="AI Migration Backend", version="1.0")

# ✅ CORS FIX — THIS IS THE KEY
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(project_detection_router)
app.include_router(project_normalization_router)
app.include_router(project_migration_planner_router)


@app.get("/health")
def health():
    return {"status": "ok"}
