import os, json, uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.database import engine, AsyncSessionLocal, Base
from app.config import settings
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.main_routers import (resume_router, coding_router, chat_router,
                                       mock_router, analytics_router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.RESUME_UPLOAD_DIR, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_problems()
    yield
    await engine.dispose()


async def seed_problems():
    from app.models import Problem
    async with AsyncSessionLocal() as db:
        if (await db.execute(select(Problem).limit(1))).scalar_one_or_none():
            return
        for path in [
            os.path.join(os.path.dirname(__file__), "..", "..", "seed", "coding_problems.json"),
            "/seed/coding_problems.json",
        ]:
            if os.path.exists(path):
                with open(path) as f:
                    data = json.load(f)
                for p in data:
                    db.add(Problem(id=uuid.uuid4(), title=p["title"], description=p["description"],
                                   difficulty=p["difficulty"], category=p["category"], tags=p.get("tags",[]),
                                   test_cases=p.get("test_cases",[]), constraints=p.get("constraints"),
                                   hints=p.get("hints",[]), solution_approach=p.get("solution_approach"),
                                   optimal_complexity=p.get("optimal_complexity"), company_tags=p.get("company_tags",[]),
                                   role_tags=p.get("role_tags",[]), times_asked=p.get("times_asked",1),
                                   last_asked_year=p.get("last_asked_year"), source=p.get("source")))
                await db.commit()
                print(f"[Seed] {len(data)} problems loaded.")
                return
        print("[Seed] coding_problems.json not found.")


app = FastAPI(title="PlacementPrep AI", version="2.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:5173","http://localhost:3000"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(resume_router, prefix="/api")
app.include_router(coding_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(mock_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}
