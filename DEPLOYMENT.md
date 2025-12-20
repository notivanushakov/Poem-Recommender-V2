# Streamlit Cloud Deployment Guide

## 🚨 IMPORTANT: Backend Requirement

**If you're seeing connection errors like:**
```
HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded
```

**This means you need to deploy the backend separately!**

👉 **See [BACKEND_DEPLOYMENT.md](BACKEND_DEPLOYMENT.md) for step-by-step instructions** to deploy the backend on Render, Railway, or Fly.io (free tiers available).

---

## Overview
This application can be deployed to Streamlit Cloud for free hosting. The app consists of:
- **Frontend**: Streamlit interface (automatically deployed)
- **Backend**: FastAPI server (needs to be deployed separately)

## ⚠️ Important Notes

### Deployment Architecture Options

#### Option 1: Streamlit Cloud (Frontend Only - Recommended for Testing)
- **What works**: Basic search functionality using embeddings
- **What doesn't work**: Backend-dependent features (explanations, translations)
- **Best for**: Quick demos, testing the interface
- **Cost**: Free

#### Option 2: Full Stack Deployment (Recommended for Production)
You'll need to deploy both frontend and backend separately:
- **Frontend**: Streamlit Cloud (free)
- **Backend**: Railway, Render, or Heroku (free tier available)
- **Best for**: Full functionality including LLM features
- **Cost**: Free tier available on most platforms

#### Option 3: Single Platform Deployment
Deploy everything on a single platform that supports both:
- **Platforms**: Railway, Render, Heroku
- **Complexity**: Medium (requires Docker or custom setup)
- **Best for**: Production with full control

## Quick Start - Streamlit Cloud (Frontend Only)

### Prerequisites
- GitHub account
- Streamlit Cloud account (free at [share.streamlit.io](https://share.streamlit.io))

### Steps

1. **Push to GitHub**
   ```bash
   # Initialize git (if not already done)
   git init
   git add .
   git commit -m "Initial commit for deployment"
   
   # Create a new repository on GitHub and push
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git branch -M main
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Select your repository
   - Set main file path: `frontend/frontend.py`
   - Click "Deploy"

3. **Configure API URL**
   - Once deployed, the app will look for backend at `http://localhost:8000`
   - Users can change this in the sidebar to point to a deployed backend

### Limitations
- Backend features (translations, explanations) won't work without a deployed backend
- Basic search and recommendations will work using the embedded data

## Full Deployment - Frontend + Backend

### Deploy Backend (Railway Example)

1. **Sign up for Railway**
   - Go to [railway.app](https://railway.app)
   - Sign in with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Configure Backend Service**
   ```bash
   # Railway will auto-detect Python
   # Ensure your backend has a start command
   ```
   
   Add to Railway settings:
   - **Start Command**: `cd backend && uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables**:
     ```
     LLM_PROVIDER=ollama
     LLM_MODEL=llama3.1
     ```

4. **Get Backend URL**
   - Railway will provide a URL like `https://your-app.railway.app`
   - Note this URL for frontend configuration

### Deploy Frontend (Streamlit Cloud)

1. **Follow steps from "Quick Start" above**

2. **Configure Backend URL**
   - In Streamlit Cloud dashboard, go to "Settings" → "Secrets"
   - Add:
     ```toml
     API_URL = "https://your-backend-url.railway.app"
     ```

3. **Update Frontend Code** (optional)
   - Modify `frontend/frontend.py` to use secrets:
   ```python
   import streamlit as st
   API_URL = st.secrets.get("API_URL", "http://localhost:8000")
   ```

## Configuration

### Environment Variables

#### Backend (.env)
```bash
# LLM Provider Configuration
LLM_PROVIDER=ollama  # or openai, anthropic, xai
LLM_MODEL=llama3.1   # model name for the provider

# Optional: API keys (not needed for ollama)
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
# XAI_API_KEY=xai-...

# Optional: Reranker model
RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
```

#### Frontend (Streamlit Secrets)
In Streamlit Cloud dashboard → Settings → Secrets:
```toml
API_URL = "https://your-backend-url.com"
```

### User-Provided API Keys
The application now supports user-provided OpenAI API keys:
- Users can enter their API key in the sidebar
- No server-side API key configuration needed for LLM features
- Backend will use the provided key for that session
- If no key provided, basic search still works

## Data Files

### Required Files
The following files must be present in your repository:
```
data/embeddings/
  ├── embeddings.npy
  ├── faiss.index
  ├── id_map.json
  ├── author_embeddings.npy
  ├── author_faiss.index
  └── author_metadata.json

data/processed/
  └── poems.parquet
```

### Large Files Warning
- GitHub has a 100MB file size limit
- Use Git LFS for large files:
  ```bash
  git lfs install
  git lfs track "*.npy"
  git lfs track "*.index"
  git lfs track "*.parquet"
  git add .gitattributes
  ```

## Testing Locally Before Deployment

1. **Start Backend**
   ```bash
   cd backend
   python app.py
   ```

2. **Start Frontend** (in separate terminal)
   ```bash
   streamlit run frontend/frontend.py
   ```

3. **Test Features**
   - Basic search (should always work)
   - Enter an OpenAI API key in sidebar
   - Test translations and explanations
   - Verify all endpoints work

## Troubleshooting

### Backend Not Responding
- Check backend logs in Railway/Render dashboard
- Verify backend URL is correct in frontend
- Check CORS settings in `backend/app.py`

### Large Files Not Uploading
- Use Git LFS for files > 50MB
- Consider hosting embeddings separately (S3, Dropbox, etc.)
- Load embeddings from URL in code

### Memory Issues
- Streamlit Cloud has 1GB RAM limit
- Backend platforms vary (Railway: 512MB-8GB depending on plan)
- Consider reducing embedding dimensions or using smaller models

### LLM Features Not Working
- Verify user entered API key in sidebar
- Check backend logs for API errors
- Ensure OpenAI package is in requirements.txt

## Cost Considerations

### Free Tiers
- **Streamlit Cloud**: Free with limitations (1GB RAM, public apps)
- **Railway**: $5 free credit per month
- **Render**: 750 hours/month free
- **Heroku**: 1000 dyno hours/month free (requires credit card)

### Paid Options
- **Streamlit Cloud**: $200/month for private apps
- **Railway**: Pay as you go ($0.000463/GB-hour)
- **Render**: $7/month for starter
- **DigitalOcean**: $5/month droplet

## Security Checklist

- [x] No API keys hardcoded in code
- [x] `.env` file in `.gitignore`
- [x] Sensitive files excluded from repo
- [x] CORS properly configured
- [x] User-provided API keys supported
- [x] Session data cached locally (not in repo)

## Recommended Deployment Strategy

For this project, I recommend:

1. **Development**: 
   - Run both frontend and backend locally
   - Use your own OpenAI API key for testing

2. **Production**:
   - Deploy frontend to Streamlit Cloud (free)
   - Keep backend local OR deploy to Railway (free tier)
   - Users provide their own OpenAI API keys
   - Basic search works without API keys

This approach:
- ✅ Costs nothing
- ✅ Keeps your API keys secure
- ✅ Allows users to use their own keys
- ✅ Basic features work for everyone
- ✅ Premium features (LLM) available for those with keys

## Support

For issues:
- Check Streamlit docs: [docs.streamlit.io](https://docs.streamlit.io)
- Railway docs: [docs.railway.app](https://docs.railway.app)
- FastAPI deployment: [fastapi.tiangolo.com/deployment](https://fastapi.tiangolo.com/deployment/)
