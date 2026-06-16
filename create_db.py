from backend.database.db import engine, Base

from backend.database.models import *

print("Creating tables...")

Base.metadata.create_all(bind=engine)

print("Done.")