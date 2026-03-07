# uvicorn fast_api:app --reload
from fastapi import FastAPI
from pymongo import MongoClient
from bson.objectid import ObjectId

app = FastAPI()

client = MongoClient("mongodb://localhost:27017/")
db = client["mydbpoc"] # database name
users_collection = db["users"] # collection name 

from pydantic import BaseModel, EmailStr

from bson.errors import InvalidId  # Import error handler

# Pydantic Model for Input Validation
class User(BaseModel):
    name: str
    sex: str
    age: int
    countery: str


@app.get("/users")
def get_users():
    users = []
    for user in users_collection.find():
        user["_id"] = str(user["_id"])  # Convert ObjectId to string
        users.append(user)
    return users

@app.post("/users")
def add_user(user:User):
    user_dict = user.dict()
    users_collection.insert_one(user_dict)
    return {"message": "User added"}


@app.put("/users/{id}")
def update_user(id: str, user: dict):
    try:
        obj_id = ObjectId(id)  # Ensure it's a valid ObjectId
    except InvalidId:
        return {"error": "Invalid ObjectId format"}
    
    users_collection.update_one({"_id": obj_id}, {"$set": user})
    return {"message": "User updated"}

@app.delete("/users/{id}")
def delete_user(id: str):
    try:
        obj_id = ObjectId(id)  # Ensure valid ObjectId
    except InvalidId:
        return {"error": "Invalid ObjectId format"}
    
    users_collection.delete_one({"_id": obj_id})
    return {"message": "User deleted"}


# ==========================================
# API INGESTION (EXTRACT) - MOCK ENDPOINTS
# ==========================================

from datetime import datetime, timedelta

# Mock Data
MOCK_CUSTOMERS = [
    {"id": 1, "name": "Alice", "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "email": "bob@example.com"},
]

MOCK_PRODUCTS = [
    {"id": 101, "name": "Laptop", "price": 1200},
    {"id": 102, "name": "Mouse", "price": 25},
]

MOCK_ORDERS = [
    {
        "order_id": 1001,
        "customer_id": 1,
        "order_date": "2026-01-02",
        "store": "Store_A",
        "updated_at": "2026-01-02T10:00:00Z",
        "items": [
            {"order_item_id": 1, "product_id": 101, "quantity": 1, "price": 1200},
            {"order_item_id": 2, "product_id": 102, "quantity": 2, "price": 25}
        ]
    },
    {
        "order_id": 1002,
        "customer_id": 2,
        "order_date": "2026-01-03",
        "store": "Store_B",
        "updated_at": "2026-01-03T11:00:00Z",
        "items": [
            {"order_item_id": 3, "product_id": 102, "quantity": 1, "price": 25}
        ]
    }
]

@app.get("/api/customers")
def get_customers():
    return MOCK_CUSTOMERS

@app.get("/api/products")
def get_products():
    return MOCK_PRODUCTS

@app.get("/api/orders")
def get_orders(since: str = None, page: int = 1, limit: int = 100):
    # Filter by updated_at if 'since' is provided
    result = MOCK_ORDERS
    if since:
        result = [o for o in result if o["updated_at"] >= since]
    
    # Pagination logic
    start = (page - 1) * limit
    end = start + limit
    return result[start:end]

@app.get("/api/order-items")
def get_order_items(order_id: int):
    order = next((o for o in MOCK_ORDERS if o["order_id"] == order_id), None)
    if order:
        return order["items"]
    return []
