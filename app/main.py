from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.middleware import LoggingMiddleware
from db.mongodb import close_mongo_connection, connect_to_mongo
from router.course_router import router as course_router
from router.lesson_router import router as lesson_router
from router.progress_router import router as progress_router
from router.question_router import router as question_router
from router.quiz_router import router as quiz_router
from router.submission_router import router as submission_router
from router.user_router import router as user_router
from router.payments import router as payments_router
from webhooks.stripe_webhook import router as stripe_webhook_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()


app = FastAPI(
    title="Smart Learning Assessment Platform API",
    description="Quizzes, questions, graded submissions and learner progress.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(LoggingMiddleware)

app.include_router(quiz_router)
app.include_router(question_router)
app.include_router(submission_router)
app.include_router(progress_router)
app.include_router(course_router)
app.include_router(lesson_router)
app.include_router(user_router)
app.include_router(payments_router)
app.include_router(stripe_webhook_router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
