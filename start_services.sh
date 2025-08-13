#!/bin/bash

# Start PhatThinhVina Services
echo "Starting PhatThinhVina Services..."

# Function to cleanup background processes on exit
cleanup() {
    echo "Stopping services..."
    pkill -f "flask run"
    pkill -f "react-scripts start"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start Flask backend
echo "Starting Flask backend..."
cd backend
source venv/bin/activate
python -m flask run &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start React frontend
echo "Starting React frontend..."
cd ../frontend
npm start &
FRONTEND_PID=$!

echo "Services started!"
echo "Backend: http://localhost:5000"
echo "Frontend: http://localhost:3000"
echo "Press Ctrl+C to stop all services"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
