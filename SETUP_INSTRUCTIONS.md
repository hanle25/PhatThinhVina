# PhatThinhVina Setup Instructions

## Prerequisites
- Python 3.13+ 
- Node.js 18+ and npm
- Git

## Quick Start

### Option 1: Use the automated script (Recommended)
```bash
./start_services.sh
```

### Option 2: Manual setup

#### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start Flask server:
   ```bash
   python -m flask run
   ```

#### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install Node.js dependencies:
   ```bash
   npm install
   ```

3. Start React development server:
   ```bash
   npm start
   ```

## Accessing the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000

## Troubleshooting

### Common Issues

1. **"No module named flask"**
   - Make sure you're in the virtual environment: `source venv/bin/activate`
   - Reinstall dependencies: `pip install -r requirements.txt`

2. **"react-scripts: command not found"**
   - Install Node.js dependencies: `npm install`

3. **Port already in use**
   - Kill existing processes: `pkill -f "flask run"` or `pkill -f "react-scripts start"`

4. **Database connection issues**
   - Check if the database file exists: `ls instance/app.db`
   - Run database migrations if needed

### Stopping Services
- Press `Ctrl+C` in each terminal window
- Or use the automated script which handles cleanup automatically

## Development Notes
- The backend uses SQLite database stored in `instance/app.db`
- CORS is enabled for development
- The frontend proxies API requests to the backend
