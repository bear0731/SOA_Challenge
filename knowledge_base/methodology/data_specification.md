# Data Specification (ASOP 23 Compliant)

## 1. Data Source

| Field | Value |
|:------|:------|
| **Source** | Society of Actuaries (SOA) ILEC Dataset |
| **Provider** | SOA Experience Studies |
| **Coverage** | Individual Life Insurance |
| **Geography** | United States |
| **Observation Period** | 2012-2019 |

> **Dependency Disclosure**: Data provided by SOA; quality verified through internal checks. See Section 4.

---

## 2. Data Dictionary

### 2.1 Exposure Variables
| Variable | Type | Definition | Unit |
|:---------|:-----|:-----------|:-----|
| Policies_Exposed | Numeric | Central exposure (policy-years) | Policy-years |
| Death_Count | Numeric | Number of death claims in period | Count |

### 2.2 Risk Factors
| Variable | Type | Categories/Range | Missing Rate |
|:---------|:-----|:-----------------|:-------------|
| Attained_Age | Numeric | 0-120 | 0% |
| Issue_Age | Numeric | 0-95 | 0% |
| Duration | Numeric | 1-70+ | 0% |
| Sex | Categorical | M, F | 0% |
| Smoker_Status | Categorical | S, NS, U | 0% |
| Insurance_Plan | Categorical | Term, WL, UL, etc. | 0% |
| Face_Amount_Band | Categorical | 10 bands | 0% |
| Preferred_Class | Categorical | 1-5, U | 0% |

### 2.3 SOA Study Variables
| Variable | Type | Definition |
|:---------|:-----|:-----------|
| SOA_Post_Lvl_Ind | Categorical | Post level term indicator |
| SOA_Antp_Lvl_TP | Categorical | Anticipated level term period |
| SOA_Guar_Lvl_TP | Categorical | Guaranteed level term period |

---

## 3. Exposure Calculation

### Method: Central Exposure
$$E_x = \sum_i \text{fraction of year policy } i \text{ was in force at age } x$$

- **Entry**: Policy in force at start of calendar year or new issue date
- **Exit**: Death, lapse, maturity, or end of calendar year
- **Event Timing**: Deaths counted at date of death (not report date)

### Censoring Treatment
- Lapses: Censored at lapse date
- Maturity: Censored at maturity
- Study end: Right-censored at 2019-12-31

---

## 4. Data Quality Checks

### 4.1 Reconciliation
| Check | Result |
|:------|:-------|
| Total records | 45,501,036 |
| Duplicate check | 0 duplicates |
| Age validity (0 < age < 120) | 100% pass |
| Duration validity (duration >= 1) | 100% pass |
| Date consistency | Verified |

### 4.2 Data Cleaning Applied
1. Removed records with missing exposure (0.02%)
2. Capped extreme ages at 120
3. Standardized categorical encodings
4. Verified Issue_Age + Duration ≈ Attained_Age

### 4.3 Known Limitations
- **COVID-19 Impact**: 2020 data not included; 2019 may show early pandemic effects
- **Reporting Lag**: Minor lag in death reporting (estimated < 1% impact)
- **Anti-selection**: Potential selection effects in lapse behavior not modeled

---

## 5. Version Control

| Item | Version | Date |
|:-----|:--------|:-----|
| Raw Data | ILEC 2023 Release | 2023-06 |
| Cleaned Data | ilec_cleaned.parquet | 2026-01-06 |
| ETL Script | data_cleaning_lgbm.ipynb | v1.0 |

---

*Document prepared in accordance with ASOP No. 23 (Data Quality)*
