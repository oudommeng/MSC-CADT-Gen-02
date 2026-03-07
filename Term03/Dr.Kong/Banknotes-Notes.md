# Banknote Authentication Dataset — Quiz Prep

## 1. What Is This Dataset?

Real dataset from UCI Machine Learning Repository.  
Task: **Binary classification** — detect forged banknotes from genuine ones.  
Method used to create features: **Wavelet Transform** applied to images of banknotes.

---

## 2. Dataset Structure

| Property | Value |
|----------|-------|
| Total samples | 1372 |
| Features | 4 |
| Classes | 2 (0 = genuine, 1 = forged) |
| Class distribution | ~762 genuine (0), ~610 forged (1) |

---

## 3. Features Explained

```
variance, skewness, curtosis, entropy, class
```

| Feature | What It Measures |
|---------|-----------------|
| `variance` | Spread of wavelet-transformed pixel values |
| `skewness` | Asymmetry of the distribution of pixel values |
| `curtosis` | "Peakedness" of the distribution (how sharp vs. flat) |
| `entropy` | Randomness/disorder in the image texture |
| `class` | **Label**: `0` = genuine, `1` = forged |

All 4 features are **continuous (float)** values — not raw pixel data.

---

## 4. Sample Rows

```
variance,  skewness,  curtosis,  entropy,  class
-0.89569,  3.0025,    -3.6067,   -3.4457,  1   ← forged
 3.4769,  -0.15314,    2.53,      2.4495,  0   ← genuine
 3.9102,   6.065,     -2.4534,   -0.68234, 0   ← genuine
```

**Pattern you can notice:**
- Genuine (0) often has **higher positive variance**
- Forged (1) often has **lower/negative variance**
- Not a perfect rule — that's why ML is needed

---

## 5. Why Wavelet Transform?

Wavelet transform breaks an image into frequency components.  
Each component captures different texture/edge patterns.  
From those components → compute variance, skewness, curtosis, entropy.  
This gives compact, meaningful features instead of raw thousands of pixels.

---

## 6. Classification Algorithms That Fit This Dataset

| Algorithm | Why It Works |
|-----------|-------------|
| Logistic Regression | Simple, good baseline for binary classification |
| SVM | Works well on small, clean feature sets |
| Decision Tree / Random Forest | Handles non-linear boundaries |
| KNN | Works on numeric features |
| Neural Network | Overkill here but works |

---

## 7. Key ML Concepts This Dataset Tests

### Train/Test Split
```python
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
```

### Feature Scaling (important!)
Variance ranges from ~-7 to +7, entropy from ~-8 to +3 — different scales.  
Use `StandardScaler` or `MinMaxScaler` before distance-based algorithms (KNN, SVM).

### Evaluation Metrics
| Metric | Formula | When to Use |
|--------|---------|-------------|
| Accuracy | correct / total | When classes balanced |
| Precision | TP / (TP + FP) | When false positives costly |
| Recall | TP / (TP + FN) | When false negatives costly |
| F1 Score | 2 * P * R / (P + R) | Balance precision & recall |

For banknotes: **recall on forged (class 1)** matters most — missing a fake is bad.

---

## 8. Confusion Matrix

```
                Predicted Genuine   Predicted Forged
Actual Genuine       TN                  FP
Actual Forged        FN                  TP
```

- **FP** = called genuine but actually forged → BAD (fake slips through)
- **FN** = called forged but actually genuine → annoying but less harmful

---

## 9. Likely Quiz Questions

**Q: What does class=0 mean?**  
Genuine banknote.

**Q: What does class=1 mean?**  
Forged/counterfeit banknote.

**Q: How many features does the dataset have?**  
4 — variance, skewness, curtosis, entropy.

**Q: How were the features extracted?**  
Wavelet transform applied to banknote images.

**Q: Why do we need feature scaling?**  
Features have different ranges. Scaling ensures no single feature dominates distance calculations (important for KNN, SVM).

**Q: What is curtosis?**  
A measure of how "peaked" a distribution is. High curtosis = sharp peak. Low curtosis = flat distribution.

**Q: What is skewness?**  
Measure of asymmetry of the distribution. Positive = tail on right. Negative = tail on left.

**Q: What is entropy in this context?**  
Measure of disorder/randomness in the image texture. High entropy = more random/noisy texture.

**Q: Which metric is most important for this problem?**  
Recall for class 1 (forged) — we don't want to miss a counterfeit note.

**Q: What type of ML problem is this?**  
Supervised learning, binary classification.

---

## 10. Quick Feature Pattern Summary

```
Genuine (0):  variance tends HIGH (+), skewness HIGH (+)
Forged  (1):  variance tends LOW (negative), entropy tends LOW (negative)
```

Not absolute rules — overlaps exist, which is why we need classifiers not just thresholds.
