# Quick Reference Card

## 🚀 Start Your System

### Terminal 1: Start API
```bash
python -m src.api.app
# Runs on http://127.0.0.1:5000
```

### Terminal 2: Start Dashboard
```bash
python -m streamlit run streamlit_dashboard.py
# Runs on http://localhost:8501
```

---

## 📌 Essential Files

| File | Purpose |
|------|---------|
| `DEPLOYMENT_GUIDE.md` | Deploy to Render, AWS, Railway |
| `API_TESTING_GUIDE.md` | Test all API endpoints |
| `Postman_Collection.json` | Import into Postman for testing |
| `requirements.txt` | All dependencies (updated) |
| `src/api/schemas.py` | Input validation with Pydantic |
| `src/utils/structured_logging.py` | Logging system |

---

## 🧪 Test API with curl

### Health Check
```bash
curl http://127.0.0.1:5000/health
```

### Make Prediction
```bash
curl -X POST http://127.0.0.1:5000/predict \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-local-key" \
  -d '{
    "days_signup_age": 180,
    "recency_days": 15,
    "frequency_total": 45,
    "session_duration_avg": 12.5,
    "feature_count_used": 8,
    "device_type": "desktop",
    "os_type": "windows",
    "user_segment": "premium",
    "region": "north"
  }'
```

---

## 📊 View Logs

```bash
# API logs
tail -f logs/api.log

# Audit trail (prediction records)
tail -f logs/audit.jsonl

# Filtered: Only predictions
tail -f logs/api.log | grep prediction_made
```

---

## 🎯 Key Metrics

- **Accuracy**: 91.36%
- **API Latency**: <50ms
- **Rate Limit**: 100 req/min
- **Test Coverage**: 7 scenarios

---

## 📱 Access Dashboard

Open browser: `http://localhost:8501`

**Pages**:
1. 📈 Dashboard - System metrics
2. 🔮 Predictions - Test form
3. 📊 Metrics - Performance
4. ℹ️ About - Project info

---

## ☁️ Deploy (Pick One)

### Render (Easiest)
```bash
# 1. Push to GitHub
git push origin main

# 2. Create service at https://render.com
# 3. Connect GitHub repo
# 4. Done! ✅
```

### AWS EC2
```bash
# Follow DEPLOYMENT_GUIDE.md section: AWS EC2
# Takes ~30 mins for full setup
```

### Railway
```bash
# 1. Connect GitHub
# 2. Add PostgreSQL plugin
# 3. Deploy
# Takes ~5 mins
```

---

## 🔧 Update Dependencies

```bash
pip install -r requirements.txt --upgrade
```

---

## ✅ Pre-Presentation Checklist

- [ ] Dashboard loads at localhost:8501
- [ ] API responds at 127.0.0.1:5000
- [ ] Predictions work end-to-end
- [ ] Postman tests pass
- [ ] Logs are being created
- [ ] Deployment guide is ready
- [ ] Accuracy: 91.36% ✅

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| API won't start | Check port 5000: `lsof -i :5000` |
| Dashboard can't connect | Ensure API running first |
| Import errors | Install deps: `pip install -r requirements.txt` |
| Logs missing | Create: `mkdir -p logs` |
| Model not found | Train: `python src/models/train_model.py` |

---

## 💬 What to Say in Interview

**"I took a basic ML project and made it production-ready by:**

1. **Adding input validation** - Pydantic schemas for type safety
2. **Building logging system** - Structured JSON logs + audit trails
3. **Creating test suite** - Postman collection with 7 test scenarios
4. **Writing deployment guides** - Ready for Render, AWS, or Railway
5. **Documenting everything** - Complete guides for testing and deployment

**Result**: An enterprise-grade system that's ready to deploy to production."

---

## 📚 Documentation

- **UPGRADES_SUMMARY.md** - What was added (this file)
- **DEPLOYMENT_GUIDE.md** - How to deploy everywhere
- **API_TESTING_GUIDE.md** - Complete API documentation
- **Postman_Collection.json** - Ready-to-use test suite

---

**Last Updated**: April 26, 2026
**Status**: ✅ Production Ready
