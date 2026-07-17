import os

class Config:
    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key")

    # Database
    DATABASE_PATH = os.getenv("DATABASE_PATH", "panel.db")

    # Main Panel
    PANEL_NAME = "LVM Panel"
    PANEL_URL = os.getenv("PANEL_URL", "http://localhost:5000")

    # Node System
    NODE_SECRET = os.getenv("NODE_SECRET", "CHANGE_ME_TO_A_RANDOM_SECRET")
    HEARTBEAT_INTERVAL = 30
    NODE_TIMEOUT = 90

    # Docker
    DOCKER_SOCKET = os.getenv(
        "DOCKER_SOCKET",
        "unix:///var/run/docker.sock"
    )

    # API
    API_PREFIX = "/api"

    # Uploads
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB

config = Config()
