# User Drop-Off Detection in Web Applications
## Quick Start Guide

### 📋 Project Overview
This project uses Machine Learning to detect users who are likely to leave (drop-off) a web application, enabling proactive intervention strategies.

**Goal:** Build a predictive model that identifies at-risk users 30 days before they become inactive.

---

## 🚀 QUICK START (Next 30 Minutes)

### Step 1: Read the Roadmap
Open `PROJECT_ROADMAP.md` - It contains your complete guide with every tiny step.

### Step 2: Create Project Structure
```bash
# Run these commands in your terminal

# Create directories
mkdir data data\raw data\processed
mkdir src src\data src\features src\models src\evaluation src\api src\dashboard src\utils
mkdir notebooks
mkdir models
mkdir results
mkdir docs
mkdir tests
```

### Step 3: Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate  # On Windows
# or
source venv/bin/activate  # On MacOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Verify Installation
```bash
python -c "import pandas; import sklearn; print('✓ All packages installed!')"
```

---

## 📚 How to Use This Project

1. **Read First:** Start with `PROJECT_ROADMAP.md` - it guides every single step
2. **Follow Phase by Phase:** Don't skip ahead - each phase builds on the previous
3. **Code Along:** Create scripts as described in the roadmap
4. **Test Frequently:** Work incrementally and test after each phase
5. **Document Everything:** Write comments explaining your code

---

## 🎯 Key Phases at a Glance

| Phase | Duration | Focus |
|-------|----------|-------|
| **1** | Week 1 | Setup & Planning |
| **2-3** | Week 2-3 | Data Collection & Analysis |
| **4-5** | Week 4-5 | Feature Engineering & Preprocessing |
| **6-7** | Week 6-7 | Model Development |
| **8-9** | Week 8-9 | Tuning & Evaluation |
| **10-12** | Week 10-12 | Deployment & Documentation |

---

## 📁 What Each Folder Means

```
user-dropoff-detection/
├── data/               ← Store datasets here
├── src/                ← All your code goes here
├── notebooks/          ← Jupyter notebooks for exploration
├── models/             ← Saved trained models
├── results/            ← Plots, metrics, outputs
├── docs/               ← Documentation
└── tests/              ← Unit & integration tests
```

---

## 💡 First Real Task (Phase 1)

1. **Create data directory structure** ✓ (done above)
2. **Create config.yaml** - Configuration file
3. **Start first Jupyter notebook** - For data exploration

---

## ❓ Questions?

Refer to the `PROJECT_ROADMAP.md` - it has answers to everything!

---

**Next Step:** Open `PROJECT_ROADMAP.md` and start with Phase 1! 🎉

---

## ✅ Ready-to-Run Implementation Added

This repository now includes a complete beginner-friendly implementation:

- `STEP_BY_STEP_IMPLEMENTATION.md` - Full execution guide for your project title
- `run_pipeline.py` - Run full ML pipeline in one command
- `src/data/generate_synthetic_data.py` - Synthetic data generator
- `src/features/build_features.py` - Feature dataset builder
- `src/models/train_model.py` - Model training script
- `src/evaluation/evaluate_model.py` - Evaluation script
- `src/api/app.py` - Flask API for prediction

Quick demo command:

```bash
python run_pipeline.py
```
