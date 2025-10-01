# Quick Start Guide

Get your refactored backend running in **5 minutes**! ⚡

## Prerequisites

- ✅ Python 3.11+ installed
- ✅ MongoDB running
- ✅ `uv` package manager installed

## Steps

### 1. Navigate to Directory
```bash
cd /home/houtj/projects/hill_sequence/hill_backend_v2
```

### 2. Copy Environment File
```bash
cp ../hill_backend/.env .env
```

### 3. Add New Required Variables

Edit `.env` and add these two lines:

```bash
# Generate a random secret key (or use any random string)
API_SECRET_KEY=your-random-secret-key-change-this-in-production

# Use the old hardcoded password or create a new one
DOWNLOAD_API_PASSWORD=NPeGBxS4hmP8NJh4H4C0BDuQnR6B4pT2ySEHmiNVi0WDbeTJfHdiuT0BNtuyyMUN1cDenSkk9M2tKVJ0rSaxY8zo8OcGPg5o
```

### 4. (Optional) Rename Azure Variables

If your `.env` has these old names, rename them:

```bash
# OLD → NEW
API_KEY → AZURE_OPENAI_API_KEY
API_ENDPOINT → AZURE_OPENAI_ENDPOINT
API_VERSION → AZURE_OPENAI_API_VERSION
```

Or just add the new names alongside the old ones.

### 5. Run the Application
```bash
uv run python main.py
```

That's it! 🎉

## Verify It's Working

1. **Open browser** to http://localhost:8001/
   - Should see: `{"hello": "world", "version": "2.0.0", "status": "healthy"}`

2. **Check API docs** at http://localhost:8001/docs
   - Interactive Swagger UI

3. **Test an endpoint**:
   ```bash
   curl http://localhost:8001/userInfo
   ```

## Running Both V1 and V2

To run both versions simultaneously (for migration):

**Terminal 1 - V1 (port 8000)**:
```bash
cd /home/houtj/projects/hill_sequence/hill_backend
python main.py
```

**Terminal 2 - V2 (port 8001)**:
```bash
cd /home/houtj/projects/hill_sequence/hill_backend_v2
uv run python main.py
```

Now you can test both and gradually migrate!

## Update Your Frontend

Change your API base URL from:
```javascript
const API_URL = 'http://localhost:8000';
```

To:
```javascript
const API_URL = 'http://localhost:8001';
```

## Troubleshooting

### Port 8001 already in use?
```bash
# Option 1: Use different port
PORT=8002 uv run python main.py

# Option 2: Kill process on port 8001
lsof -ti:8001 | xargs kill -9
```

### MongoDB connection error?
```bash
# Check if MongoDB is running
sudo systemctl status mongodb

# Or start it
sudo systemctl start mongodb
```

### Import errors?
```bash
# Make sure dependencies are installed
uv sync

# Make sure you're running with uv
uv run python main.py
```

### Missing .env variables?
```bash
# Check your .env file has all required variables:
cat .env | grep -E "MONGODB_URL|API_SECRET_KEY|DOWNLOAD_API_PASSWORD|AZURE"
```

## Next Steps

- ✅ Test all your endpoints
- ✅ Run through your typical workflows
- ✅ Check the logs (they're now in JSON format!)
- ✅ Read [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for full migration process
- ✅ Read [README.md](README.md) for comprehensive documentation

## Common Commands

```bash
# Run in development mode (auto-reload)
uv run uvicorn main:app --reload --port 8001

# Run in production mode
uv run uvicorn main:app --host 0.0.0.0 --port 8001 --workers 4

# Check logs (JSON format)
uv run python main.py 2>&1 | tee app.log

# Run with specific .env file
uv run --env-file .env.production python main.py
```

## Success Checklist

- [ ] Application starts without errors
- [ ] Can access http://localhost:8001/
- [ ] Can access http://localhost:8001/docs
- [ ] MongoDB connection successful
- [ ] Can create a project via API
- [ ] Can upload a file
- [ ] WebSocket chat works
- [ ] All your typical workflows work

If all checked, you're good to go! 🚀

---

**Need help?** Check [README.md](README.md) or [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)

