from fastapi import FastAPI
from app.database import engine, Base
from app.users.router import router as user_router
from app.rooms.router import router as rooms_router
from app.bookings.router import router as bookings_router
from app.payments.router import router as payments_router  # Import the payments router
from loguru import logger
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Hotel Management System",
    description="An API for managing hotel operations including guests, reservations, rooms, and payments.",
    version="1.0.0",
)



# Allow CORS for the frontend React app running on localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or use ["*"] for all origins (less secure)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)



# Set up logging
logger.add("app.log", rotation="500 MB", level="DEBUG")

# Database initialization
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)  # Create all tables in the database
    

app.include_router(user_router, prefix="/user", tags=["Users"])
app.include_router(rooms_router, prefix="/rooms", tags=["Rooms"])
app.include_router(bookings_router, prefix="/bookings", tags=["Bookings"])
app.include_router(payments_router, prefix="/payments", tags=["Payments"])  # Include the new payments routes
