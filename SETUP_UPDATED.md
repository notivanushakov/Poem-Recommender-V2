# Quick Setup Guide - Updated

## What's Changed

### ✅ User-Provided API Keys
- **OpenAI API key input** added to sidebar
- No need to configure `.env` with your API keys anymore
- Users can enter their own keys for premium features

### ✅ Fallback Support
- **Basic search works without API key**
- Explanations and translations require API key
- Clear indicators show which features are available

### ✅ GitHub & Deployment Ready
- All sensitive data removed from code
- `.gitignore` properly configured
- Streamlit deployment configurations added

## Running the Application

### 1. Start Backend (Terminal 1)
```powershell
& C:\Users\Ivan\Documents\venv\Scripts\Activate.ps1
cd backend
python app.py
```

### 2. Start Frontend (Terminal 2)
```powershell
& C:\Users\Ivan\Documents\venv\Scripts\Activate.ps1
streamlit run frontend/frontend.py
```

### 3. Using the App
1. Open http://localhost:8501
2. **(Optional)** Enter OpenAI API key in sidebar
   - Without key: Basic search works
   - With key: Full features (translations, explanations)
3. Search for poems or authors

## Features Availability

| Feature | Without API Key | With API Key |
|---------|----------------|--------------|
| Poem Search | ✅ Yes | ✅ Yes |
| Author Search | ✅ Yes | ✅ Yes |
| Recommendations | ✅ Yes | ✅ Yes |
| LLM-Powered Intent | ❌ No | ✅ Yes |
| Explanations | ❌ No | ✅ Yes |
| Translations | ❌ No | ✅ Yes |
| Bilingual Display | ❌ Limited | ✅ Yes |

## Deploying to GitHub

### First Time Setup
```powershell
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Ready for deployment - API keys externalized"

# Create repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

### Regular Updates
```powershell
git add .
git commit -m "Your commit message"
git push
```

## Deploying to Streamlit Cloud

See `DEPLOYMENT.md` for full details.

**Quick version:**
1. Push code to GitHub (above)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click "New app"
4. Select your repo
5. Set main file: `frontend/frontend.py`
6. Deploy!

**Note:** On Streamlit Cloud, users will need to:
- Enter their OpenAI API key in the sidebar OR
- Use basic search features without LLM

## File Structure Changes

```
New/Modified Files:
├── .streamlit/
│   └── config.toml          # Streamlit configuration
├── DEPLOYMENT.md            # Deployment guide
├── Procfile                 # For platform deployment
├── .gitignore               # Updated (includes .streamlit_cache)
├── frontend/frontend.py     # Added API key input
└── backend/app.py          # Added API key header support
```

## Security Notes

✅ **Safe to push to GitHub:**
- No API keys in code
- `.env` files ignored
- Cache directories ignored
- User secrets in sidebar only

❌ **Never commit:**
- `.env` files
- API keys in code
- `.streamlit_cache/` directory
- Personal tokens

## Troubleshooting

### "Service unavailable" errors
- No API key entered in sidebar
- Solution: Enter OpenAI API key OR use basic search

### Backend connection failed
- Backend not running
- Solution: Start backend first (see step 1 above)

### Features not working on deployment
- Backend not deployed OR API key not provided
- Solution: See DEPLOYMENT.md for full stack deployment

## Next Steps

1. ✅ Test locally with API key
2. ✅ Test locally without API key (basic features)
3. ✅ Push to GitHub
4. ✅ Deploy frontend to Streamlit Cloud
5. (Optional) Deploy backend to Railway/Render

## Questions?

- **Deployment**: See `DEPLOYMENT.md`
- **Architecture**: See `docs/ARCHITECTURE.md`
- **Usage**: See `docs/USAGE.md`
