def print_name(name: str) -> None:
    print(f"Hello, {name}!")

print_name("John")

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}