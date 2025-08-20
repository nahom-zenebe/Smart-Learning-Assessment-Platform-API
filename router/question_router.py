
from fastapi import APIRouter, HTTPException
from services.question_service import QuestionService
from models.Question import Question



router=APIRouter(prefix='/question',tags=["Lessons"])
serivce=QuestionService()



@router.post('/',response_model=Question,status_code=status.HTTP_201_CREATED)
async def create_Quesion(question:Question):
    question=await serivce.create_Question(question)

@router.get('/',response_model=[Question],status_code=status.HTTP_200_OK)
async def get_lesson():
    return await service.getall_Question()


@router.put('/{question_id}',response=[Question])
async def update_question(question_id:str,question:Question):
    updated=await service.update_Question(question,question_id)
    if not updated:
        raise HTTPException(status_code=404,detail="Question is Not Found")
    return updated


@router.delete("/{question_id}")
async def delete_question(question_id:str):
    deleted = await service.delete_Question(question_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Question not found")
    return deleted

