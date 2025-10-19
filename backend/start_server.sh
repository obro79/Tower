#!/bin/bash
# Start the FastAPI server accessible from other devices on the network
cd "$(dirname "$0")"
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
