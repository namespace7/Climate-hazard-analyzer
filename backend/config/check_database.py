from database import check_database_connection

if check_database_connection():
    print("MongoDB connection successful")
else:
    print("MongoDB connection failed")