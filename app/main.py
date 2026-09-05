from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.middleware import (
    JWTAuthMiddleware,
    LoggingMiddleware,
    RateLimitMiddleware,
    RoleAccessMiddleware,
)
from db.mongodb import close_mongo_connection, connect_to_mongo
from router.analytics_router import router as analytics_router
from router.course_router import router as course_router
from router.lesson_router import router as lesson_router
from router.notification_router import router as notification_router
from router.progress_router import router as progress_router
from router.question_router import router as question_router
from router.quiz_router import router as quiz_router
from router.submission_router import router as submission_router
from router.user_router import router as user_router
from router.payments import router as payments_router
from router.ws_router import router as ws_router
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

# Middleware order matters in Starlette: the LAST one added is the OUTERMOST.
# Execution order on the way in: RateLimit -> JWTAuth -> RoleAccess -> Logging.
app.add_middleware(LoggingMiddleware)
app.add_middleware(RoleAccessMiddleware)
app.add_middleware(JWTAuthMiddleware)
app.add_middleware(RateLimitMiddleware)

app.include_router(analytics_router)
app.include_router(notification_router)
app.include_router(ws_router)
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
