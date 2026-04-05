#!/usr/bin/env bash

echo "🚀 Starting bot..."
python -m bot.live_bot &

echo "🚀 Starting Streamlit..."
streamlit run main.py --server.port=$PORT --server.address=0.0.0.0