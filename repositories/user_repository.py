from app.db import db
from app.models.User import UserInDB


class UserRepository:
    def __init__(self):
        self.collection=db['users']

    def create_user(self,user:UserInDB):
        result=self.collection.insert_one(user)
        user.id=str(result.inserted_id)
        return user

    def get_by_email(self,email:str):
        user_data=self.collection.find_one({"email":email})

        if user_data:
            user_data["id"]=str(user_data["_id"])
            return UserInDB(**user_data)

        return None

    
    def 