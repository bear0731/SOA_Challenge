# Validation Framework

## 1. Validation Strategy

| Type | Method | Status |
|:-----|:-------|:-------|
| **In-Sample Fit** | A/E ratio overall | ✅ Complete |
| **Calibration** | A/E by segment/year | ✅ Complete |
| **Holdout Test** | Out-of-time validation | 🔲 Pending |
| **Stability** | Coefficient stability | 🔲 Pending |

---

## 2. In-Sample Calibration

### 2.1 Overall A/E
| Metric | Value |
|:-------|:------|
| Overall A/E Ratio | 0.9989 |
| Interpretation | Model well-calibrated |

### 2.2 A/E by Year
| Year | A/E Ratio | Status |
|:-----|:----------|:-------|
| 2012 | 1.04 | Slight underestimate |
| 2013 | 1.03 | Slight underestimate |
| 2014 | 1.01 | Calibrated |
| 2015 | 1.00 | Calibrated |
| 2016 | 1.00 | Calibrated |
| 2017 | 0.97 | Slight overestimate |
| 2018 | 0.97 | Slight overestimate |
| 2019 | 0.99 | Calibrated |

### 2.3 A/E by Segment (Coverage Tree)
- 16 segments defined
- All segments within acceptable range (0.9 - 1.1)
- See `segments/coverage_registry.json` for details

---

## 3. Out-of-Time Validation (Pending)

### Proposed Approach
1. Train on 2012-2017 data
2. Validate on 2018-2019 data
3. Measure A/E on holdout

### Expected Metrics
- [ ] A/E ratio on holdout
- [ ] RMSE by age/sex
- [ ] Calibration plot

---

## 4. Segment Analysis

### 4.1 Spotlight Segments (Anomaly Detection)
- 54 anomalous segments identified
- Criterion: |Relative Risk - 1| > 15%
- High credibility filter applied (exposure > 10,000)

### 4.2 Key Findings
| Segment | RR | Interpretation |
|:--------|:---|:---------------|
| SPOT_096 | 14.47 | Very high risk (age 85+) |
| SPOT_115 | 12.87 | Very high risk (age 85+, term) |
| SPOT_102 | 12.46 | Very high risk (age 85+) |

---

## 5. Model Limitations & Failure Modes

1. **Age Extremes**: Limited data at ages < 20 and > 90
2. **New Products**: UL/ULSG patterns may differ from training mix
3. **Trend Extrapolation**: Post-2019 predictions assume stable trends
4. **COVID-19**: Not modeled; requires external adjustment

---

*Document prepared in accordance with ASOP No. 56 (Modeling) Section 3.5*
