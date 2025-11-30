# ✅ Quick Deployment Checklist - Backend

**Location**: `JobmateAI-Backend/docs/DEPLOYMENT/QUICK_CHECKLIST.md`  
**Purpose**: Fast reference checklist for backend deployment  
**Audience**: Quick reference during deployment  
**Date**: November 30, 2025

---

## 🎯 Pre-Deployment

- [ ] Supabase account created
- [ ] Render account created
- [ ] GitHub repository access confirmed
- [ ] All team members have access

---

## 📋 Step 1: Database (Supabase)

- [ ] Account created at https://supabase.com
- [ ] New project created: `jobmate-ai`
- [ ] Database password set and saved
- [ ] Connection URL retrieved from Settings → Database
- [ ] Password replaced in URL (no `[YOUR-PASSWORD]` placeholder)
- [ ] **URL saved**: `postgresql://postgres:XXX@db.xxx.supabase.co:5432/postgres`

**Time**: ~15 minutes

---

## 📋 Step 2: Backend (Render)

- [ ] Account created at https://render.com
- [ ] Web Service created
- [ ] GitHub repo connected: `iwstech3/JobmateAI-Backend`
- [ ] Branch selected: `main`

**Configuration**:
- [ ] Name: `jobmate-ai-backend`
- [ ] Root Directory: `Backend` ⚠️
- [ ] Build Command: `pip install -r requirements.txt`
- [ ] Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [ ] Plan: Free

**Environment Variables**:
- [ ] `DATABASE_URL` = (Supabase URL from Step 1)
- [ ] `ENVIRONMENT` = `production`
- [ ] `SECRET_KEY` = (generated random key)

**Deployment**:
- [ ] Service created
- [ ] Deployment completed (5-10 min wait)
- [ ] Backend URL received: `https://xxx.onrender.com`
- [ ] Root endpoint tested: `/` returns JSON
- [ ] Docs endpoint tested: `/docs` shows Swagger UI

**Time**: ~20 minutes

---

## 📋 Step 3: CI/CD (GitHub Actions)

- [ ] Workflow file created: `.github/workflows/deploy-backend.yml`
- [ ] File committed to repository
- [ ] File pushed to branch: `deployment/ci-cd-setup`
- [ ] Workflow visible in Actions tab
- [ ] Test: Small change pushed to main
- [ ] Workflow runs successfully
- [ ] Render auto-redeploys (verified)

**Time**: ~10 minutes

---

## 📋 Step 4: Verification

- [ ] Backend API accessible: `https://xxx.onrender.com/`
- [ ] API docs accessible: `https://xxx.onrender.com/docs`
- [ ] Health check works: `https://xxx.onrender.com/health`
- [ ] Render logs show no errors
- [ ] Database connection successful (check logs)
- [ ] Environment variables all set correctly
- [ ] GitHub Actions workflow runs on push

**Time**: ~5 minutes

---

## 📝 Important Information to Document

After deployment, save these:

### URLs:
- **Backend**: `https://xxx.onrender.com`
- **API Docs**: `https://xxx.onrender.com/docs`
- **Supabase Dashboard**: https://supabase.com/dashboard
- **Render Dashboard**: https://dashboard.render.com

### Database:
- **Supabase Project**: `jobmate-ai`
- **Connection URL**: `postgresql://...` (keep secret!)

### Environment Variables (Render):
- `DATABASE_URL` = `postgresql://...`
- `ENVIRONMENT` = `production`
- `SECRET_KEY` = `xxx...`

---

## 🆘 Quick Troubleshooting

### Backend won't start?
1. Check Root Directory = `Backend`
2. Check Start Command is correct
3. Check Render logs for errors

### Database connection fails?
1. Verify `DATABASE_URL` has real password (not placeholder)
2. Check Supabase project is active
3. Verify URL format is correct

### GitHub Actions not working?
1. Check file is in `.github/workflows/`
2. Check YAML syntax
3. Verify webhook enabled in Render

---

## ⏱️ Total Time Estimate

- **Database Setup**: 15 minutes
- **Backend Deployment**: 20 minutes
- **CI/CD Setup**: 10 minutes
- **Verification**: 5 minutes
- **Total**: ~50 minutes

---

**Created by**: Miss Winny (Project Mentor)  
**Date**: November 30, 2025

