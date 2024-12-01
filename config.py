import os

APP = {}
APP["period"] = int(os.getenv("PERIOD", "1"))

# redis configurations
REDIS = {
    "host": str(os.getenv("REDIS_IP", "10.0.100.20")),
    "port": int(os.getenv("REDIS_PORT", "6379")),
}

# serial configurations
TARGET = {
    "host": str(os.getenv("TARGET_HOST", "10.0.100.20")),
    "port": int(os.getenv("TARGET_PORT", "6501")),
}