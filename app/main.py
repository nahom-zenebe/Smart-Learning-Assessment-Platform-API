from fastapi import FastAPI


from db.mongodb import  connect_to_mongo,close_mongo_connection
from router.lesson_router import router as lesson_router
from router.course_router import router as course_router
from router.question_router import router as question_router
from router.user_router import router as user_router
from app.routes import payments
from app.webhooks import stripe_webhook
from fastapi import FastAPI
from app.core.middleware import LoggingMiddleware
app=FastAPI(title="Learning Platform API")



app.include_router(lesson_router)
app.include_router(course_router)
app.include_router(question_router)
app.include_router(user_router)
app.include_router(payments.router)
app.add_middleware(LoggingMiddleware)
app.include_router(stripe_webhook.router)

@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()


@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()