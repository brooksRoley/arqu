from server.app.config import Settings, _REPO_ROOT
import pydantic
import os
from pathlib import Path

# Unset environment variables to test
os.environ.pop("DATABASE_URL", None)
os.environ.pop("JWT_SECRET", None)
os.environ.pop("SERVER_ENCRYPTION_KEY", None)

env_path = _REPO_ROOT / ".env"
print(f"Checking for .env at: {env_path}")
print(f"File exists? {env_path.exists()}")

try:
    s = Settings()
    print("Settings loaded successfully")
except pydantic.ValidationError as e:
    for error in e.errors():
        print(f"Field: {error['loc'][0]}, Type: {error['type']}")
