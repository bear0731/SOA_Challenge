# Model Specification (ASOP 56 Compliant)

## 1. Model Overview

| Field | Value |
|:------|:------|
| **Model Name** | ILEC Mortality Prediction Model |
| **Type** | Gradient Boosted Decision Tree (LightGBM) |
| **Objective** | Poisson regression with exposure offset |
| **Target** | Mortality rate (deaths per policy-year) |
| **Purpose** | Individual life mortality experience analysis |

---

## 2. Model Architecture

### 2.1 Algorithm: LightGBM
- **Framework**: Microsoft LightGBM
- **Objective Function**: Poisson deviance with log-link
- **Offset**: log(Policies_Exposed) for proper rate estimation

### 2.2 Hyperparameters

| Parameter | Value | Rationale |
|:----------|:------|:----------|
| n_estimators | 100 | Balance fit vs overfitting |
| max_depth | 6 | Limit complexity, improve interpretability |
| learning_rate | 0.1 | Standard, allows sufficient trees |
| min_child_samples | 100 | Credibility threshold (~100 lives) |
| reg_alpha (L1) | 0.1 | Feature selection regularization |
| reg_lambda (L2) | 1.0 | Shrinkage regularization |
| subsample | 0.8 | Reduce variance |
| colsample_bytree | 0.8 | Feature bagging |

### 2.3 Parameter Selection Rationale

1. **Poisson Objective**: Appropriate for count data with varying exposure; naturally handles rate estimation
2. **max_depth=6**: Provides sufficient complexity for interactions while maintaining interpretability; deeper trees showed diminishing returns
3. **min_child_samples=100**: Ensures credibility (~100 expected deaths minimum per leaf); aligns with actuarial credibility standards
4. **Regularization**: L1+L2 combination prevents overfitting; parameters selected via cross-validation

---

## 3. Feature Engineering

### 3.1 Features Used
| Feature | Type | Transformation | Selection Rationale |
|:--------|:-----|:---------------|:--------------------|
| Attained_Age | Numeric | None | Primary mortality driver |
| Issue_Age | Numeric | None | Underwriting selection |
| Duration | Numeric | None | Select period effect |
| Sex | Categorical | Label encoded | Mortality differential |
| Smoker_Status | Categorical | Label encoded | Major risk factor |
| Insurance_Plan | Categorical | Label encoded | Product mix effect |
| Face_Amount_Band | Categorical | Label encoded | Socioeconomic proxy |
| Preferred_Class | Categorical | Label encoded | Underwriting class |
| SOA_Post_Lvl_Ind | Categorical | Label encoded | Term structure |
| SOA_Antp_Lvl_TP | Categorical | Label encoded | Term structure |
| SOA_Guar_Lvl_TP | Categorical | Label encoded | Term structure |

### 3.2 Features NOT Included
| Feature | Reason for Exclusion |
|:--------|:--------------------|
| Observation_Year | Handled via year factors post-model |
| Geographic region | Not available in ILEC |
| Premium band | Highly correlated with Face_Amount |

---

## 4. Year Factor Adjustment

### Two-Stage Approach
1. **Stage 1**: Train base model ignoring year
2. **Stage 2**: Calculate A/E by year, apply as multiplicative factors

### Year Factors
| Year | Factor | Interpretation |
|:-----|:-------|:---------------|
| 2012 | 1.0425 | Higher than average |
| 2013 | 1.0261 | Higher than average |
| 2014 | 1.0073 | Near average |
| 2015 | 0.9979 | Near average |
| 2016 | 0.9993 | Near average |
| 2017 | 0.9716 | Lower than average |
| 2018 | 0.9679 | Lower than average |
| 2019 | 0.9893 | Near average |

---

## 5. Model Interpretation

### 5.1 SHAP Values
Model interpretability provided through TreeSHAP:
- Global feature importance ranking
- Local explanations for individual predictions

### 5.2 Feature Importance (Global)
| Rank | Feature | Mean |SHAP| |
|:-----|:--------|:--------------------|
| 1 | Attained_Age | Highest impact |
| 2 | Duration | High impact |
| 3 | Smoker_Status | High impact |
| 4 | Issue_Age | Moderate impact |
| 5 | Face_Amount_Band | Moderate impact |

---

## 6. Model Limitations

1. **Extrapolation Risk**: Model may not perform well for ages/durations outside training range
2. **COVID-19**: Not trained on pandemic data; use caution for 2020+ predictions
3. **Interaction Complexity**: Tree-based model captures interactions but may miss subtle patterns
4. **Categorical Encoding**: Label encoding may introduce artificial ordering

---

## 7. Model Governance

| Item | Value |
|:-----|:------|
| Model File | `lgbm_mortality_offset_poisson.txt` |
| Training Date | 2026-01-05 |
| Version | 1.0 |
| Peer Review | Pending |

---

*Document prepared in accordance with ASOP No. 56 (Modeling)*
