"""
Vercel Serverless Function Entrypoint for Faslyn Agricultural REST API.
======================================================================
Exposes Faslyn's machine-to-machine BRICS AgriN endpoints on Vercel:
  - GET /api/v1/health
  - GET /api/v1/export
  - GET /api/v1/telemetry
  - GET /api/v1/satellite
  - GET /api/v1/soil
  - GET /api/v1/hubs
"""

import os
import sys

# Ensure repository root is on Python module search path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.api import FaslynApiHandler

# Vercel's Python runtime requires a class named 'handler'
handler = FaslynApiHandler
