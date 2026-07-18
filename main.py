from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
import bcrypt  # 👈 1. Import bcrypt directly instead of passlib
from pydantic import BaseModel

# Configuration
import os
# Fallback to a dummy key only for local testing, require an env var in production
SECRET_KEY = os.getenv("SECRET_KEY", "local-insecure-fallback-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
users_db = {}

# --- Update these helper functions ---

def hash_password(password: str) -> str:
    # Turn string to bytes, generate salt, and hash it
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')  # Decode back to string to store in DB


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Convert both back to bytes and check them
    plain_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(plain_bytes, hashed_bytes)

# --- Keep everything else exactly the same ---


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except jwt.PyJWTError:
        raise credentials_exception


# --- ROUTES ---

# 1. Signup / Register
@app.post("/signup")
def signup(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username in users_db:
        raise HTTPException(status_code=400, detail="Username already registered")

    users_db[form_data.username] = {
        "username": form_data.username,
        "password": hash_password(form_data.password)
    }
    return {"message": "User created successfully"}


# 2. Login (Generates Token)
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}


# 3. Protected Route (Requires Authentication)
@app.get("/users/me")
def read_users_me(current_user: str = Depends(get_current_user)):
    return {"message": f"Hello {current_user}, this is a secured endpoint!"}

@app.get("/contact")
def contact():
    return {"message": "hello world from contact"}

class UserData(BaseModel):
    username: str
    email: str

@app.post("/contact_2")
def contact_2(data: UserData):
    # You can access the values using data.username and data.email
    return {
        "message": f"Hello {data.username}, we received your email: {data.email}"
    }

@app.patch("/contact_3")
def contact_3(data: UserData):
    # You can access the values using data.username and data.email
    return {
        "message": f"Hello {data.username}, we received your email: {data.email}"
    }


@app.put("/contact_4")
def contact_4(data: UserData):
    # You can access the values using data.username and data.email
    return {
        "message": f"Hello {data.username}, we received your email: {data.email}"
    }

import os
from fastapi import FastAPI, Depends
from dotenv import load_dotenv
# 1. Update the import statement
from google import genai

load_dotenv()

app = FastAPI()

# 2. Initialize the modern GenAI Client
# It will look for your GEMINI_API_KEY environment variable automatically.
# Alternatively, pass it directly: client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
client = genai.Client()


@app.post("/ask-ai")
def ask_gemini(prompt: str):
    try:
        # Swap the old model for the 3.5 generation
        response = client.models.generate_content(
            model='gemini-3.5-flash',  # <-- Update this line
            contents=prompt,
        )
        return {"status": "success", "response": response.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}

from pydantic import BaseModel

# 1. Define the structural schema for incoming data
class AIQueryRequest(BaseModel):
    prompt: str
    temperature: float = 0.7  # Allows you to control AI randomness

    # 2. Update your endpoint to consume the Pydantic schema
@app.post("/ask-ai")
def ask_ai(request: AIQueryRequest, current_user: str = Depends(get_current_user)):
    # You now access the validated text cleanly using dot-notation
    user_prompt = request.prompt
    ai_randomness = request.temperature

    # Execute your Gemini API call logic here...
    response_text = call_gemini(prompt=user_prompt, temp=ai_randomness)

    return {"user": current_user, "response": response_text}