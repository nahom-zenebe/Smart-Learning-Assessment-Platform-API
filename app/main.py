from Fastapi import FastAPI
from db.mongodb import  connect_to_mongo,close_mongo_connection
from routers.lesson_router import router as lesson_router


app=FastAPI(title="Learning Platform API")



app.include_router(lesson_router)


@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()


@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()