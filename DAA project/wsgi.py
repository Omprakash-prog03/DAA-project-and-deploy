# ===================================================================
# WSGI/ASGI entry point for PythonAnywhere deployment
#
# Option A (Recommended - ASGI mode):
#   Point PythonAnywhere ASGI app to: backend.main:app
#
# Option B (WSGI mode):
#   Point PythonAnywhere WSGI app to: wsgi:application
# ===================================================================

import os
from backend.main import app

# Allow all origins for PythonAnywhere (the domain is dynamic)
os.environ.setdefault("CORS_ORIGINS", "*")

# For WSGI mode, export the app directly
# PythonAnywhere handles ASGI -> WSGI conversion
application = app
