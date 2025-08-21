from dotenv import load_dotenv
import os



load_dotenv()

MONGODB_URL= os.getenv("MONGO_URI")
JWT_SECRET = os.getenv("JWT_SECRET")
STRIPE_SECRET_KEY= os.getenv('STRIPE_API_KEY')
STRIPE_WEBHOOK_SECRET= os.getenv('STRIPE_WEBHOOK_SECRET')
ACCESS_TOKEN_EXPIRE_MINUTES = 60