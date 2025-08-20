from repositories.course_repository import CourseRepository
from models.Question import Question




class QuestionService:
    def __init__(self):
        self.question=QuestionRepository()


    async def create_Question(self,question:Question):
        question_data = question.dict(by_alias=True)
        question_id=await self.question.create(question)return await self.course.get_by_id(course_id)
        return question_id


    async def getall_Question(self):
        return await self.question.getallquestion()



    async def update_Question(self,question:Question,quesiton_id:str):
        return await self.question.update(question,quesiton_id)

    async def delete_Question(self,question_id:str):
        return await self.question.deleteQuestion(question_id)



        


