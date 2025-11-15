"""
Configuration settings for Vehicle Damage Detection System
"""

import os

# Roboflow API Configuration
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY", "DvmKUUSUrM8rQBeil5V2")
ROBOFLOW_MODEL_ID = os.getenv("ROBOFLOW_MODEL_ID", "car-damage-detection-5ioys-4z3z4/2")

# Server Configuration
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 7860))
FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", 8000))

# Model Configuration
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", 0.25))

# Application Settings
APP_TITLE = "AI-Powered Vehicle Damage Detection"
APP_DESCRIPTION = "Automated vehicle damage assessment using AI for car rental inspection"
VERSION = "1.0.0"
