#!/usr/bin/env python3
"""
run.py — Quick start script for TSRTC SmartTicket
Usage: python run.py
"""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import app, init_db

if __name__ == '__main__':
    # Create database folder if not exists
    os.makedirs(os.path.join(os.path.dirname(__file__), 'database'), exist_ok=True)

    # Initialize database
    init_db()

    print("=" * 50)
    print("  🚌 TSRTC SmartTicket — Hyderabad")
    print("  http://localhost:5000")
    print("=" * 50)

    # Get port from Render environment, default to 5000 locally
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)