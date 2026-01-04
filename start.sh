#!/bin/bash
echo "🧠 Starting NeuroFlash Application"
echo "=================================="

# Start backend
echo "Starting backend server..."
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 5

# Start frontend
echo "Starting frontend..."
cd ../frontend
npm start &
FRONTEND_PID=$!

echo ""
echo "✅ NeuroFlash is running!"
echo "📱 Frontend: http://localhost:8080"
echo "🔧 Backend API: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for user interrupt
wait

# Cleanup
echo "Stopping servers..."
kill $BACKEND_PID
kill $FRONTEND_PID