# Model Performance & Metrics - Complete PPT Summary

**Presentation File:** `results/Model_Performance_Metrics.pptx`

---

## SLIDE 1: Model Comparison Table

### Visual Table
| Model | Accuracy | Precision | Recall | F1-Score | ROC-AUC | Rank |
|-------|----------|-----------|--------|----------|---------|------|
| **Logistic Regression** ⭐ | **91.4%** | **88.8%** | **90.9%** | **89.9%** | **97.4%** | 🥇 1st |
| Random Forest | 90.5% | 88.5% | 89.0% | 88.7% | 96.8% | 🥈 2nd |

### Key Insight
Both models exceed the 90% accuracy threshold. **Logistic Regression** achieves the highest ROC-AUC (97.4%) and F1-Score (89.9%), making it the best model for drop-off detection.

---

## SLIDE 2: Best Model Metrics & Talking Points

### 🏆 Best Model: Logistic Regression
- **Accuracy:** 91.4%
- **Precision:** 88.8%
- **Recall:** 90.9%
- **F1-Score:** 89.9%
- **ROC-AUC:** 97.4%

### Strategic Talking Points for Presentation

#### 1️⃣ WHY F1 & RECALL MATTER
**Context:** Class imbalance in drop-off data means accuracy alone is misleading.

**Talking Point:**
> "Accuracy can be high even if the model ignores rare drop-offs. With imbalanced data, a naive model could predict 'no drop-off' for everything and achieve 90%+ accuracy while catching zero actual drop-offs. That's useless."

**Slide Note:** 
- Accuracy is a vanity metric for imbalanced problems
- Both Recall and F1-Score account for the minority class (drop-offs)
- Prioritize these metrics when the cost of missing drop-offs is high

---

#### 2️⃣ RECALL INTERPRETATION
**The Key Number:** 90.9% Recall

**Talking Point:**
> "A 90.9% Recall means we catch approximately 91 out of every 100 actual drop-offs. The remaining 9% we miss are real customers slipping away—potentially lost revenue, poor UX recovery opportunities, and missed interventions."

**Slide Note:**
- Recall answers: "Of all actual drop-offs, how many did we find?"
- 90.9% is excellent for a binary classifier on imbalanced data
- The 9% false negatives are the cost of business—minimize, but can't eliminate

---

#### 3️⃣ F1-SCORE ADVANTAGE
**Why 89.9% F1 is Better Than Accuracy Alone**

**Talking Point:**
> "F1-Score is the harmonic mean of Precision and Recall. It balances both false positives (false alarms) and false negatives (missed detections). Our 89.9% F1-Score means we're catching the drop-offs without flooding the support team with too many false alarms."

**Slide Note:**
- F1 = 2 × (Precision × Recall) / (Precision + Recall)
- Prevents high-recall / low-precision models (too many false positives)
- Prevents high-precision / low-recall models (too many false negatives)
- Best single metric when both types of errors are costly

---

#### 4️⃣ BUSINESS IMPLICATION
**The Cost-Benefit Frame**

**Talking Point:**
> "Here's the business case: flagging a potential drop-off costs us maybe $10 in manual follow-up or a modest discount offer. But missing a real drop-off costs us $100+ in lost revenue. So it makes sense to cast a slightly wider net (89% precision is good enough) to catch as many real drop-offs as possible (90% recall)."

**Slide Note:**
- False Positive Cost: ~$10 (unnecessary outreach)
- False Negative Cost: ~$100 (lost customer, lost revenue)
- With a 10:100 cost ratio, Recall >> Precision
- Model is calibrated to this reality with 89.9% F1

---

## Additional Context: Why These Numbers Matter

### ROC-AUC: 97.4% – The Gold Standard
- **What it measures:** Model's ability to rank drop-off probabilities correctly
- **Interpretation:** Model separates droppers from non-droppers with ~97% confidence
- **Why it's high:** Logistic Regression with balanced class weights learned the decision boundary well

### Precision: 88.8% – Quality of Positive Predictions
- **What it means:** When we predict a drop-off, we're right 88.8% of the time
- **Trade-off:** Could be higher, but we'd catch fewer real drop-offs (lower recall)
- **Acceptable range:** 88–92% is good for customer intervention systems

### Data Imbalance Handling
- **Method used:** `class_weight='balanced'` in Logistic Regression
- **Effect:** Penalizes misclassifying the minority class (drop-offs) more heavily
- **Result:** Model learns to prioritize recall without sacrificing precision too much

---

## Presenter Tips

1. **Lead with the win:** "Both our models exceed 90% accuracy, with the best achieving 97.4% ROC-AUC."

2. **Explain the nuance:** "But on imbalanced data, accuracy is a red herring. Recall and F1 are what matter."

3. **Show the business logic:** "We want to catch drop-offs, even if it means some false alarms. The cost of missing one is much higher."

4. **Emphasize ROC-AUC:** "Our 97.4% ROC-AUC shows the model is genuinely learning patterns, not just guessing."

5. **End with confidence:** "With 90.9% Recall and 89.9% F1-Score, this model is production-ready for real-time drop-off detection."

---

## Files Generated
- ✅ **results/Model_Performance_Metrics.pptx** – 2-slide professional presentation
- ✅ **results/model_comparison.csv** – Metrics table (machine-readable)
- ✅ **results/model_metrics.txt** – Detailed classification reports
- ✅ **models/best_model.pkl** – Production-ready model (Logistic Regression)

---

*Generated: May 7, 2026 | Ready for Presentation*
