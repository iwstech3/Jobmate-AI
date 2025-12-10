# 🔄 GitHub Actions Explained - Backend

**Location**: `JobmateAI-Backend/docs/DEPLOYMENT/GITHUB_ACTIONS_EXPLAINED.md`  
**Purpose**: Detailed explanation of CI/CD workflows for backend  
**Audience**: Team members learning CI/CD  
**Date**: November 30, 2025

---

## 📚 Table of Contents

1. [What is GitHub Actions?](#what-is-github-actions)
2. [How It Works](#how-it-works)
3. [Understanding the Workflow File](#understanding-the-workflow-file)
4. [Step-by-Step Breakdown](#step-by-step-breakdown)
5. [How Automatic Deployment Works](#how-automatic-deployment-works)
6. [Troubleshooting](#troubleshooting)

---

## 🎯 What is GitHub Actions?

### Definition

**GitHub Actions** is a built-in automation tool in GitHub that allows you to run scripts automatically when certain events happen in your repository.

### Why Use It?

| Benefit | Explanation |
|---------|-------------|
| **Automation** | No manual steps - everything happens automatically |
| **Consistency** | Same process every time - reduces human error |
| **Time Saving** | Deploy in seconds instead of minutes |
| **Free** | Included with GitHub - no extra cost |
| **Visibility** | See what's happening in real-time |

### Real-World Analogy

Think of GitHub Actions like a **smart assistant**:
- You push code → Assistant detects it
- Assistant runs tests → Makes sure code works
- Assistant deploys → Puts code online
- Assistant notifies you → Tells you if it worked

**Without GitHub Actions**: You'd have to do all these steps manually every time.

---

## 🔧 How It Works

### The Flow

```
1. You push code to GitHub
   ↓
2. GitHub detects the push
   ↓
3. GitHub Actions workflow triggers
   ↓
4. Workflow runs on a virtual machine
   ↓
5. Workflow executes steps (test, build, etc.)
   ↓
6. Workflow notifies Render (via webhook)
   ↓
7. Render redeploys your application
```

### Key Components

1. **Workflow File** (`.yml` file)
   - **What**: Defines what to do
   - **Where**: `.github/workflows/` folder
   - **Format**: YAML (human-readable configuration)

2. **Trigger** (event that starts workflow)
   - **What**: Push, pull request, schedule, etc.
   - **Example**: Push to `main` branch

3. **Job** (set of steps)
   - **What**: Runs on a virtual machine
   - **Example**: "Deploy to Render" job

4. **Step** (single action)
   - **What**: One command or action
   - **Example**: "Install dependencies"

---

## 📄 Understanding the Workflow File

### File Location

**Path**: `.github/workflows/deploy-backend.yml`

**Why this location?**:
- `.github/` = Special folder GitHub recognizes
- `workflows/` = Contains workflow definitions
- `.yml` = YAML file extension (not `.yaml`)

**Important**: GitHub only recognizes workflows in this exact location!

### File Structure Overview

```yaml
name: Workflow Name          # What shows in GitHub UI
on:                         # When to trigger
  push:                     # Event type
jobs:                       # What to do
  job-name:                 # Job definition
    steps:                   # Steps to execute
```

---

## 🔍 Step-by-Step Breakdown

Let's break down our workflow file line by line:

### 1. Workflow Name

```yaml
name: Deploy Backend to Render
```

**What it is**: The name shown in GitHub Actions tab

**Why it matters**: Helps identify this workflow among others

**Can be**: Any descriptive name you want

---

### 2. Triggers

```yaml
on:
  push:
    branches:
      - main
    paths:
      - 'Backend/**'
      - '.github/workflows/deploy-backend.yml'
  workflow_dispatch:
```

**Breaking it down**:

**`on:`** = "When should this workflow run?"

**`push:`** = "When code is pushed to repository"

**`branches: - main`** = "Only on the main branch"
- **Why main?**: This is our production branch
- **What if other branch?**: Workflow won't run (saves resources)

**`paths: - 'Backend/**'`** = "Only if files in Backend folder change"
- **Why?**: Don't redeploy if only documentation changes
- **`**`** = All files and subfolders

**`paths: - '.github/workflows/deploy-backend.yml'`** = "Or if workflow file itself changes"
- **Why?**: If we update the workflow, we want to test it

**`workflow_dispatch:`** = "Allow manual triggering from GitHub UI"
- **Why?**: Sometimes you want to run it manually
- **How?**: Go to Actions tab → Click workflow → Click "Run workflow"

---

### 3. Jobs

```yaml
jobs:
  deploy:
    name: Deploy to Render
    runs-on: ubuntu-latest
```

**Breaking it down**:

**`jobs:`** = "List of jobs to run"
- Can have multiple jobs (run in parallel or sequence)

**`deploy:`** = "Name of this job"
- Can be anything: `build`, `test`, `deploy`, etc.

**`name: Deploy to Render`** = "Display name"
- Shows in GitHub UI
- More descriptive than job name

**`runs-on: ubuntu-latest`** = "Virtual machine to use"
- **What is a virtual machine?**: A computer in the cloud
- **Why Ubuntu?**: Linux operating system (free, reliable)
- **Why latest?**: Always uses newest Ubuntu version

**Other options**: `windows-latest`, `macos-latest` (but we use Ubuntu for Python)

---

### 4. Steps

Each step does one thing. Let's go through them:

#### Step 1: Checkout Code

```yaml
- name: Checkout code
  uses: actions/checkout@v4
```

**What it does**: Downloads your code from GitHub to the virtual machine

**Why needed**: The virtual machine starts empty - needs your code to work with

**`uses: actions/checkout@v4`**:
- **`uses`** = "Use a pre-built action"
- **`actions/checkout`** = Official GitHub action for downloading code
- **`@v4`** = Version 4 (specific version, not latest - more reliable)

**Without this step**: Workflow can't access your code!

---

#### Step 2: Set up Python

```yaml
- name: Set up Python
  uses: actions/setup-python@v4
  with:
    python-version: '3.11'
```

**What it does**: Installs Python 3.11 on the virtual machine

**Why needed**: Our backend is written in Python - needs Python to run

**`with:`** = "Parameters for this action"

**`python-version: '3.11'`** = "Install Python 3.11"
- **Why 3.11?**: Matches what we're using locally
- **Why specific version?**: Ensures consistency (same version everywhere)

**Without this step**: Can't run Python code!

---

#### Step 3: Install Dependencies

```yaml
- name: Install dependencies
  working-directory: ./Backend
  run: |
    python -m pip install --upgrade pip
    pip install -r requirements.txt
```

**What it does**: Installs all Python packages our backend needs

**Breaking it down**:

**`working-directory: ./Backend`**:
- **What**: Change to Backend folder first
- **Why**: Our `requirements.txt` is in Backend folder
- **Without this**: Can't find requirements.txt!

**`run: |`**:
- **What**: Run shell commands
- **`|`** = Multi-line command (allows multiple lines)

**`python -m pip install --upgrade pip`**:
- **What**: Update pip (Python package installer) to latest version
- **Why**: Ensures we have latest features and bug fixes

**`pip install -r requirements.txt`**:
- **What**: Install packages listed in requirements.txt
- **Why**: Backend needs FastAPI, SQLAlchemy, etc. to run
- **`-r`** = "Read from file"

**Without this step**: Missing packages = application won't run!

---

#### Step 4: Run Tests (Future)

```yaml
- name: Run tests (if available)
  working-directory: ./Backend
  run: |
    # Uncomment when tests are added
    # pytest tests/ || true
    echo "Tests will be added later"
  continue-on-error: true
```

**What it does**: Runs tests to verify code works (currently placeholder)

**Why commented out**: We don't have tests yet, but structure is ready

**`continue-on-error: true`**:
- **What**: Don't fail workflow if this step fails
- **Why**: Tests are optional for now (will be required later)

**Future**: When tests are added, uncomment and remove `continue-on-error`

---

#### Step 5: Notify Deployment

```yaml
- name: Notify deployment
  run: |
    echo "✅ Backend deployment triggered!"
    echo "Render will automatically redeploy from GitHub"
    echo "Check Render dashboard for deployment status"
```

**What it does**: Prints messages to workflow logs

**Why**: Provides visibility - you can see what's happening

**`echo`** = Print text (shows in GitHub Actions logs)

**This is informational only** - doesn't actually deploy (Render's webhook does that)

---

#### Step 6: Deployment Status

```yaml
- name: Deployment Status
  run: |
    echo "🚀 Backend is being deployed to Render"
    echo "📊 Check deployment status at: https://dashboard.render.com"
```

**What it does**: More informational messages

**Why**: Reminds you where to check deployment status

---

## 🔄 How Automatic Deployment Works

### The Complete Flow

```
┌─────────────────┐
│  You push code  │
│  to GitHub      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ GitHub detects  │
│ the push        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ GitHub Actions  │
│ workflow runs   │
│ (verifies code) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Render webhook  │
│ is triggered    │
│ (automatic)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Render redeploys│
│ your service    │
└─────────────────┘
```

### Render's Auto-Deploy

**Important**: Render has its own auto-deploy feature!

When you connect a GitHub repository to Render:
1. Render creates a **webhook**
2. Webhook listens for pushes to GitHub
3. When you push, webhook notifies Render
4. Render automatically redeploys

**So why GitHub Actions?**

GitHub Actions adds:
- ✅ **Testing**: Run tests before deployment
- ✅ **Verification**: Check code quality
- ✅ **Visibility**: See what's happening in GitHub
- ✅ **Consistency**: Same process every time

**Both work together**:
- GitHub Actions: Verifies and tests
- Render Webhook: Actually deploys

---

## 🛠️ Setting Up GitHub Actions

### Step 1: Create the Workflow File

**Location**: `.github/workflows/deploy-backend.yml`

**How to create**:
1. In your repository, create folder: `.github/workflows/`
2. Create file: `deploy-backend.yml`
3. Copy the workflow content (already provided)

**Important**: 
- Folder must be exactly `.github` (with dot)
- File must be `.yml` (not `.yaml`)
- Must be in `workflows/` subfolder

---

### Step 2: Commit and Push

**Why**: GitHub only runs workflows that are in the repository

**Steps**:
```bash
# Make sure you're on the right branch
git checkout deployment/ci-cd-setup

# Add the workflow file
git add .github/workflows/deploy-backend.yml

# Commit
git commit -m "Add GitHub Actions workflow for backend deployment"

# Push
git push origin deployment/ci-cd-setup
```

**Expected**: File is now in GitHub repository

---

### Step 3: Verify in GitHub

**Steps**:
1. Go to your repository on GitHub
2. Click "Actions" tab (top navigation)
3. You should see "Deploy Backend to Render" workflow listed

**If you see it**: ✅ Workflow is active!

**If you don't see it**:
- Check file location (must be `.github/workflows/`)
- Check file extension (must be `.yml`)
- Check you committed and pushed

---

### Step 4: Test the Workflow

**Steps**:
1. Make a small change (e.g., update README)
2. Commit and push to `main` branch
3. Go to "Actions" tab
4. Click on the workflow run
5. Watch it execute in real-time

**What you'll see**:
- Each step running
- Logs from each step
- Success ✅ or failure ❌

---

## 🐛 Troubleshooting

### Problem: Workflow Not Appearing in Actions Tab

**Symptoms**: 
- Created workflow file but don't see it in Actions tab

**Solutions**:
1. **Check file location**:
   - Must be: `.github/workflows/deploy-backend.yml`
   - Not: `github/workflows/` (missing dot)
   - Not: `.github/workflow/` (wrong folder name)

2. **Check file extension**:
   - Must be: `.yml`
   - Not: `.yaml` (GitHub prefers `.yml`)

3. **Check you committed**:
   - File must be committed to repository
   - Check: `git status` (should show file as committed)

4. **Check branch**:
   - Workflow might only be on a feature branch
   - Merge to `main` to see it in Actions tab

---

### Problem: Workflow Not Triggering

**Symptoms**:
- Workflow exists but doesn't run when pushing

**Solutions**:
1. **Check trigger conditions**:
   ```yaml
   on:
     push:
       branches:
         - main  # Only runs on main branch
   ```
   - Are you pushing to `main`?
   - Or are you on a different branch?

2. **Check paths**:
   ```yaml
   paths:
     - 'Backend/**'  # Only runs if Backend files change
   ```
   - Did you change files in `Backend/` folder?
   - Or only other files?

3. **Check YAML syntax**:
   - Use online YAML validator
   - Common errors: indentation, missing colons

---

### Problem: Workflow Fails

**Symptoms**:
- Workflow runs but shows red ❌ (failed)

**Solutions**:
1. **Check logs**:
   - Click on failed workflow run
   - Click on failed job
   - Expand failed step
   - Read error message

2. **Common errors**:

   **"Cannot find requirements.txt"**:
   - **Cause**: `working-directory` is wrong
   - **Fix**: Should be `./Backend`

   **"Python not found"**:
   - **Cause**: Python setup step failed
   - **Fix**: Check Python version in workflow

   **"Import error"**:
   - **Cause**: Missing dependency
   - **Fix**: Check `requirements.txt` includes all packages

3. **Test locally**:
   - Run same commands on your computer
   - If they fail locally, they'll fail in workflow

---

### Problem: Render Not Redeploying

**Symptoms**:
- Workflow runs successfully but Render doesn't redeploy

**Solutions**:
1. **Check Render webhook**:
   - Go to Render dashboard
   - Settings → Webhooks
   - Verify webhook is active

2. **Check branch**:
   - Render might be watching different branch
   - Verify in Render settings

3. **Manually trigger**:
   - In Render, click "Manual Deploy"
   - This redeploys immediately

**Note**: Render's webhook is separate from GitHub Actions. Both can work independently.

---

## 📊 Understanding Workflow Logs

### How to Read Logs

1. **Go to Actions tab**
2. **Click on a workflow run**
3. **Click on a job** (e.g., "Deploy to Render")
4. **Expand steps** to see details

### Log Structure

```
✓ Checkout code (2s)
  → Checking out code...
  → Code checked out

✓ Set up Python (5s)
  → Installing Python 3.11...
  → Python installed

✓ Install dependencies (30s)
  → Installing packages...
  → FastAPI installed
  → SQLAlchemy installed
  → ...

✓ Notify deployment (1s)
  → ✅ Backend deployment triggered!
```

### What to Look For

- **Green checkmark** ✅ = Step succeeded
- **Red X** ❌ = Step failed
- **Yellow circle** 🟡 = Step in progress
- **Gray circle** ⚪ = Step skipped

---

## 🎓 Best Practices

### 1. Use Specific Versions

```yaml
uses: actions/checkout@v4  # ✅ Good - specific version
uses: actions/checkout@latest  # ❌ Bad - might break
```

**Why**: Specific versions are more reliable. `@latest` might change and break your workflow.

---

### 2. Test Before Deploy

```yaml
- name: Run tests
  run: pytest tests/
```

**Why**: Catch bugs before they reach production.

---

### 3. Use Working Directory

```yaml
working-directory: ./Backend
```

**Why**: Ensures commands run in correct folder.

---

### 4. Add Error Handling

```yaml
continue-on-error: true  # Don't fail workflow if this step fails
```

**Why**: Some steps are optional (like notifications).

---

### 5. Document Your Workflows

```yaml
# This workflow deploys backend to Render
# Runs on push to main branch
# Requires Backend/ folder changes
```

**Why**: Helps team understand what workflows do.

---

## 📚 Additional Resources

### Official Documentation

- **GitHub Actions Docs**: https://docs.github.com/en/actions
- **Workflow Syntax**: https://docs.github.com/en/actions/workflows/workflow-syntax-for-github-actions
- **Pre-built Actions**: https://github.com/marketplace?type=actions

### Learning Resources

- **GitHub Actions Tutorial**: https://docs.github.com/en/actions/learn-github-actions
- **YAML Guide**: https://yaml.org/spec/1.2.2/

---

## ✅ Checklist

- [ ] Workflow file created in `.github/workflows/`
- [ ] File has correct name and extension (`.yml`)
- [ ] Workflow committed and pushed to repository
- [ ] Workflow visible in Actions tab
- [ ] Workflow triggers on push to main
- [ ] All steps execute successfully
- [ ] Render redeploys automatically
- [ ] Logs are readable and helpful

---

**Created by**: Miss Winny (Project Mentor)  
**Date**: November 30, 2025  
**Version**: 1.0



