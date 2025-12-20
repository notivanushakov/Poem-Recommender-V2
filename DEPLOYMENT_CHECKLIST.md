# Streamlit Deployment Checklist

## ✅ What Was Done (Completed)

- [x] Added environment variable support for backend URL
- [x] Added backend health check with visual indicator
- [x] Improved error messages for connection failures
- [x] Added `/health` endpoint to backend
- [x] Created comprehensive deployment guides
- [x] Added Streamlit secrets support

## 📋 What You Need To Do

### Step 1: Push Changes to GitHub
```bash
cd "C:\Users\Ivan\Documents\poem-recommender\Poem-Recommender"
git add .
git commit -m "Fix Streamlit deployment - add backend support"
git push
```

### Step 2: Deploy Backend (Choose ONE platform)

#### Option A: Render (Recommended)
1. Go to https://render.com and sign up
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `cd backend && uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free
5. Click "Create Web Service"
6. Wait for deployment (~5-10 minutes)
7. Copy your URL (e.g., `https://poem-recommender-backend.onrender.com`)

#### Option B: Railway
1. Go to https://railway.app and sign in with GitHub
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Set start command: `cd backend && uvicorn app:app --host 0.0.0.0 --port $PORT`
5. Wait for deployment
6. Copy your URL

#### Option C: Fly.io
See detailed instructions in [BACKEND_DEPLOYMENT.md](BACKEND_DEPLOYMENT.md)

### Step 3: Configure Streamlit Cloud

1. Go to your Streamlit app at https://share.streamlit.io
2. Click on your app → Settings (⚙️) → Secrets
3. Add your backend URL:
   ```toml
   BACKEND_URL = "https://your-backend-url.onrender.com"
   ```
   (Replace with your actual backend URL from Step 2)
4. Click "Save"
5. The app will automatically restart

### Step 4: Test Your Deployment

1. Visit your Streamlit app
2. Check the sidebar - should show "✅ Backend connected" (green)
3. Try a query: "find someone like pushkin"
4. Should work without errors!

### Step 5: Optional - Add OpenAI Key

If you want enhanced translation/explanation features:

1. In Streamlit Cloud → Secrets, add:
   ```toml
   OPENAI_API_KEY = "sk-your-key-here"
   ```
2. OR users can enter it directly in the UI

## 🔍 Troubleshooting

### Sidebar Shows "⚠️ Backend not available"
- Backend deployment failed or URL is wrong
- Check backend platform logs
- Verify URL in Streamlit secrets (no trailing slash, use HTTPS)
- Test backend: `curl https://your-backend-url.com/health`

### Backend Deployment Fails
- Check build logs in your hosting platform
- Common issues:
  - Missing dependencies in requirements.txt
  - Large model files not found
  - Out of memory (free tier limits)
- See [BACKEND_DEPLOYMENT.md](BACKEND_DEPLOYMENT.md) troubleshooting section

### Still Getting Connection Errors
- Clear browser cache
- Restart Streamlit app (click "Reboot app" in settings)
- Check that BACKEND_URL secret was saved correctly
- Verify backend health: visit `https://your-backend-url.com/health` in browser

### "Model files not found" in Backend
Your backend needs the embedding files from `data/embeddings/`:
- Option 1: Include files in git (if small enough)
- Option 2: Upload to cloud storage (S3/GCS) and download on startup
- Option 3: Run `rebuild_embeddings.py` during deployment
- See [BACKEND_DEPLOYMENT.md](BACKEND_DEPLOYMENT.md) for details

## 📚 Reference Files

- **[DEPLOYMENT_FIX_SUMMARY.md](DEPLOYMENT_FIX_SUMMARY.md)** - Detailed explanation of what was fixed
- **[BACKEND_DEPLOYMENT.md](BACKEND_DEPLOYMENT.md)** - Complete backend deployment guide
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - General deployment overview
- **[.streamlit/secrets.toml.example](.streamlit/secrets.toml.example)** - Example secrets configuration

## 🎯 Expected Timeline

- Push to GitHub: 1 minute
- Backend deployment: 5-15 minutes (first time)
- Streamlit configuration: 2 minutes
- Testing: 2 minutes

**Total: ~10-20 minutes**

## 💰 Cost

All recommended platforms have free tiers:
- **Render**: 750 hours/month free
- **Railway**: $5 credit/month  
- **Fly.io**: Limited free resources
- **Streamlit Cloud**: Free for public apps

**Total cost: $0** for testing/personal use

## ✅ Success Criteria

You'll know it's working when:
- ✅ Sidebar shows "✅ Backend connected" in green
- ✅ Search queries return results without errors
- ✅ No connection timeout errors
- ✅ Can see poems and authors in results

## 🚀 Next Steps After Successful Deployment

1. Test all features thoroughly
2. Share your app URL with users
3. Monitor backend logs for errors
4. Consider upgrading to paid tier for better uptime
5. Set up monitoring/alerting (optional)

## Need Help?

- Check platform-specific docs:
  - Render: https://render.com/docs
  - Railway: https://docs.railway.app
  - Fly.io: https://fly.io/docs
- Review backend logs in your hosting platform
- Test backend directly: `curl https://your-backend-url.com/health`
