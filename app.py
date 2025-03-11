from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List, Optional
from jose import JWTError, jwt
from datetime import datetime, timedelta
from uvicorn import run
from Model import User, UserCreate, Token

SECRET_KEY = "placeholder"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 35

app = FastAPI()

users_db = {
    1: {"id": 1, "name": "Rethabile", "email": "retha@gmail.com"},
    2: {"id": 2, "name": "mosa", "email": "mosa@gmail.com"}
}


admin_users = {
    "admin": {"username": "admin", "password": "admin123"}
}

oauth2 = OAuth2PasswordBearer(tokenUrl="token")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):

    to_encode = data.copy()
    expire = datetime.now() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):

    user = admin_users.get(form_data.username)
    if not user or user["password"] != form_data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}


def get_current_user(token: str = Depends(oauth2)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return username


@app.get("/users", response_model=List[User])
def get_users(page: int = Query(1, ge=1),per_page: int = Query(10, ge=1),
        name: Optional[str] = None,
        sort_by: Optional[str] = "id",
        current_user: str = Depends(get_current_user)
):

    user_list = list(users_db.values())

    if current_user != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    if name:
        user_list = [user for user in user_list if name.lower() in user["name"].lower()]

    if sort_by in ["id", "name", "email"]:
        user_list = sorted(user_list, key=lambda x: x[sort_by])

    start = (page - 1) * per_page
    end = start + per_page
    return user_list[start:end]


@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int, current_user: str = Depends(get_current_user)):

    user = users_db.get(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.post("/users", response_model=User)
def create_user(user: UserCreate, current_user: str = Depends(get_current_user)):

    if current_user != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    new_id = max(users_db.keys(), default=0) + 1
    new_user = User(id=new_id, name=user.name, email=user.email)
    users_db[new_id] = new_user.model_dump()
    return new_user


@app.put("/users/{user_id}", response_model=User)
def update_user(user_id: int, user: UserCreate, current_user: str = Depends(get_current_user)):

    if current_user != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    users_db[user_id] = {"id": user_id, "name": user.name, "email": user.email}
    return users_db[user_id]


@app.delete("/users/{user_id}")
def delete_user(user_id: int, current_user: str = Depends(get_current_user)):

    if current_user != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    del users_db[user_id]


    return {"message": "User deleted"}



if __name__ == "__main__":
   run(app, host="127.0.0.1", port=8000)

