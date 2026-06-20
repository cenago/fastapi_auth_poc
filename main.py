from fastapi import FastAPI

# Initialize the FastAPI application
app = FastAPI()

# Define a root route
@app.get("/")
def read_root():
    return {"message": "Hello World"}