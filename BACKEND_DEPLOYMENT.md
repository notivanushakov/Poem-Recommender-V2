# Backend Deployment Guide

## Problem
Your Streamlit Cloud frontend is trying to connect to `localhost:8000`, but there's no backend server running in the Streamlit Cloud environment. You need to deploy the backend separately.

## Quick Fix Options

### Option 1: Deploy Backend on Render (Recommended - Free Tier)

1. **Sign up for Render** at https://render.com

2. **Create a New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure the service:
     - **Name**: `poem-recommender-backend`
     - **Root Directory**: Leave empty (or set to `backend` if you restructure)
     - **Environment**: `Python 3`
     - **Build Command**: 
       ```bash
       pip install -r requirements.txt
       ```
     - **Start Command**: 
       ```bash
       cd backend && uvicorn app:app --host 0.0.0.0 --port $PORT
       ```
     - **Instance Type**: Free

3. **Set Environment Variables** in Render:
   - Go to Environment tab
   - Add any required API keys (e.g., `OPENAI_API_KEY`)

4. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment (5-10 minutes first time)
   - Copy your backend URL (e.g., `https://poem-recommender-backend.onrender.com`)

5. **Update Streamlit App**
   - In Streamlit Cloud settings, add environment variable:
     - `BACKEND_URL` = `https://your-backend-url.onrender.com`
   - OR: In the Streamlit app sidebar, paste your backend URL

### Option 2: Deploy Backend on Railway

1. **Sign up for Railway** at https://railway.app

2. **Create New Project**
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository

3. **Configure Service**
   - Railway will auto-detect Python
   - Add a `Procfile` if not present:
     ```
     web: cd backend && uvicorn app:app --host 0.0.0.0 --port $PORT
     ```
   - Or set start command: `cd backend && uvicorn app:app --host 0.0.0.0 --port $PORT`

4. **Add Environment Variables**
   - Click on Variables
   - Add `OPENAI_API_KEY` and other required keys

5. **Deploy and Get URL**
   - Railway generates a URL automatically
   - Copy it and use it in your Streamlit app

### Option 3: Deploy Backend on Fly.io

1. **Install Fly CLI**: https://fly.io/docs/hands-on/install-flyctl/

2. **Create `fly.toml`** in your project root:
   ```toml
   app = "poem-recommender-backend"
   
   [build]
     builder = "paketobuildpacks/builder:base"
   
   [env]
     PORT = "8080"
   
   [[services]]
     internal_port = 8080
     protocol = "tcp"
   
     [[services.ports]]
       handlers = ["http"]
       port = 80
   
     [[services.ports]]
       handlers = ["tls", "http"]
       port = 443
   ```

3. **Deploy**:
   ```bash
   fly launch
   fly deploy
   ```

4. **Set Secrets**:
   ```bash
   fly secrets set OPENAI_API_KEY=your_key_here
   ```

## After Backend Deployment

### Update Your Streamlit App

You have two options:

**Option A: Environment Variable (Recommended)**
1. Go to Streamlit Cloud → Your App → Settings → Secrets
2. Add:
   ```toml
   BACKEND_URL = "https://your-backend-url.com"
   ```
3. The app will automatically use this URL

**Option B: Manual Entry**
1. In the Streamlit app sidebar
2. Find "Backend API URL" field
3. Replace `http://localhost:8000` with your deployed backend URL
4. Click outside the field to save

## Testing Your Backend

Once deployed, test the health endpoint:

```bash
curl https://your-backend-url.com/health
```

Should return:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "poem_index_loaded": true,
  "author_index_loaded": true
}
```

## Troubleshooting

### Backend Won't Start
- **Check logs** in your hosting platform
- **Verify requirements.txt** includes all dependencies
- **Check Python version** (should be 3.9+)
- **Verify file paths** - make sure `data/embeddings/` exists with model files

### "Model files not found"
Your backend needs the embedding files. Options:
1. **Include in repo** (if files are small enough)
2. **Download during build**: Add to start script:
   ```bash
   python scripts/rebuild_embeddings.py && cd backend && uvicorn app:app --host 0.0.0.0 --port $PORT
   ```
3. **Use cloud storage**: Upload to S3/GCS and download on startup

### Frontend Still Can't Connect
1. **Check CORS**: Backend `app.py` already has CORS enabled
2. **Verify URL**: No trailing slash, use HTTPS
3. **Check backend status**: Visit `https://your-backend.com/health`
4. **Check Streamlit logs**: Look for connection errors

### "Out of Memory" on Free Tier
The embedding models are large. Options:
1. **Use smaller model**: Change `MODEL_NAME` in `app.py`
2. **Upgrade tier**: Most platforms offer affordable paid tiers
3. **Optimize loading**: Lazy load models only when needed

## Cost Estimates

- **Render Free**: 750 hours/month (sleeps after 15 min inactivity)
- **Railway Free**: $5 credit/month
- **Fly.io Free**: Limited resources, sufficient for testing
- **Heroku**: No longer has free tier

## Production Recommendations

For production use:
1. **Use paid tier** for better uptime ($7-20/month)
2. **Add monitoring** (Sentry, LogRocket)
3. **Enable caching** (Redis for response caching)
4. **Add rate limiting** (prevent abuse)
5. **Use CDN** for static assets
6. **Set up CI/CD** (auto-deploy on push)

## Alternative: Embedded Backend (Advanced)

If you want to avoid separate backend deployment, you can embed the backend logic directly in the Streamlit app. This requires significant refactoring but means you only deploy to Streamlit Cloud.

See `EMBEDDED_BACKEND_GUIDE.md` for details (to be created if needed).
