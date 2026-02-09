# 🚀 Quick Start Guide

## Installation (5 minutes)

### Step 1: Install Dependencies
```bash
python3 -m pip install -r requirements.txt
```

### Step 2: Load Sample Data
```bash
python3 load_sample_data.py
```

This creates:
- ✅ Database with schema
- ✅ 30 sample coding problems
- ✅ Demo user account
- ✅ Sample practice history

### Step 3: Start the Server

**Option A - Using the startup script:**
```bash
# Linux/Mac
./run.sh

# Windows
run.bat
```

**Option B - Manual start:**
```bash
python3 -m src.main
```

The API will start at `http://localhost:8000` (default).  
If port 8000 is busy:
```bash
PORT=8001 python3 -m src.main
# or
PORT=8001 ./run.sh
```

### Step 4: Open the Frontend

Open `frontend/index.html` in your web browser, or:

```bash
cd frontend
python3 -m http.server 8080
```

Then visit `http://localhost:8080`

## 🔐 Demo Login

Use these credentials to login:
- **Email:** `demo@example.com`
- **Password:** `demo123`

## ✅ Verify Installation

Run the test script to verify everything is working:
```bash
python3 test_installation.py
```

## 📖 What You'll See

After logging in, you'll see:

1. **Dashboard Stats**
   - Problems solved
   - Success rate
   - Current streak
   - Due revisions

2. **Personalized Recommendations**
   - Top 5 problems recommended for you
   - Explanations for why each problem is suggested
   - Based on your weaknesses and error patterns

3. **Your Weaknesses**
   - Topics/patterns where you need improvement
   - Mastery scores
   - Success rates

4. **Revision Queue**
   - Problems due for spaced repetition review
   - Based on forgetting curve

## 🎯 Try These Actions

### 1. Generate New Recommendations
Click "Generate New" button to get fresh recommendations based on current progress.

### 2. Record Practice Attempts
Use the API to log practice:

```bash
curl -X POST http://localhost:8000/api/attempts \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "problem_id": "two-sum",
    "verdict": "Accepted",
    "time_taken": 300,
    "error_type": null
  }'
```

### 3. View API Documentation
Visit `http://localhost:8000/docs` for interactive API docs (Swagger UI).  
If you changed backend port, use that port in the URL.

## 🐛 Troubleshooting

### Error: "Module not found"
```bash
python3 -m pip install -r requirements.txt
```

### Error: "Database not found"
```bash
python3 load_sample_data.py
```

### Error: "Port 8000 already in use"
Run the backend on a different port:
```bash
PORT=8001 python3 -m src.main
# or
PORT=8001 ./run.sh
```

### Frontend can't connect to API
Make sure:
1. Backend is running on the same port configured in `frontend/index.html` (`API_URL`, default: 8000)
2. Open browser console (F12) to see errors
3. Check CORS is enabled in `src/main.py`

## 📚 Next Steps

1. **Explore the Code**
   - Start with `src/main.py` for API endpoints
   - Check `src/recommender.py` for recommendation algorithm
   - Review `src/learner_model.py` for metrics calculation

2. **Customize**
   - Add your own problems to the database
   - Modify recommendation scoring weights
   - Adjust spaced repetition intervals

3. **Test Different Scenarios**
   - Create a new user account
   - Log attempts with different error types
   - Observe how recommendations change

## 📞 Need Help?

- Check `README.md` for detailed documentation
- Review Phase 1 and Phase 2 PDFs for design specs
- Contact: Anshu Sinha (anshujuly2@gmail.com)
