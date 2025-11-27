from models.database import init_db
init_db()
from app import app as handler
