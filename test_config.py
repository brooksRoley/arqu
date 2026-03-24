from server.app.config import Settings
try:
    s = Settings()
    print("Settings loaded successfully")
    print(f"database_url: {s.database_url}")
except Exception as e:
    print(e)
