from fastapi import FastAPI


from db.mongodb import  connect_to_mongo,close_mongo_connection
from router.lesson_router import router as lesson_router
from router.course_router import router as course_router
from router.question_router import router as question_router
from router.user_router import router as user_router


app=FastAPI(title="Learning Platform API")



app.include_router(lesson_router)
app.include_router(course_router)
app.include_router(question_router)
app.include_router(user_router)

@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()


@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()