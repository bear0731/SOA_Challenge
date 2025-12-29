# ILEC 死亡率資料 - 結構分析與 DAG

## 1. Observation Unit
**Policy-Year-Cell** (彙總單位，非個別保單)

每筆 = 某保單 × 觀察年度 × 特徵組合的暴險與死亡經驗

---

## 2. 因果 DAG

```mermaid
flowchart TB
    subgraph Baseline["基線特徵 (Baseline)"]
        Sex["Sex"]
        SmokerStatus["Smoker_Status"]
        IssueAge["Issue_Age"]
    end

    subgraph Underwriting["核保選擇 (Selection)"]
        PfdInd["Preferred_Indicator"]
        PfdClass["Preferred_Class"]
        NumPfdClass["Number_of_Pfd_Classes"]
    end

    subgraph Policy["保單結構"]
        InsPlan["Insurance_Plan"]
        FaceAmt["Face_Amount_Band"]
        IssueYear["Issue_Year"]
    end

    subgraph TimeVarying["時變變數 (Time-Varying)"]
        Duration["Duration"]
        AttAge["Attained_Age"]
        ObsYear["Observation_Year"]
    end

    subgraph Exposure["暴險"]
        PolExp["Policies_Exposed"]
        AmtExp["Amount_Exposed"]
    end

    subgraph Outcome["結果"]
        Death["Death_Count"]
        DeathAmt["Death_Claim_Amount"]
    end

    subgraph Expected["基準 (VBT2015)"]
        ExpDeath["ExpDth_VBT2015"]
    end

    %% 因果關係
    Sex --> Underwriting
    SmokerStatus --> Underwriting
    IssueAge --> Underwriting
    
    Baseline --> Death
    Underwriting --> Death
    
    IssueAge --> AttAge
    Duration --> AttAge
    
    AttAge --> Death
    Duration --> Death
    
    Policy --> Exposure
    Exposure --> Death
    
    %% Confounding
    IssueYear --> Duration
    IssueYear --> ObsYear
    Duration --> ObsYear
    
    %% Selection
    Baseline --> Exposure
    Underwriting --> Exposure
```

---

## 3. 時間維度識別問題 (APC Problem)

```
Attained_Age = Issue_Age + Duration
Observation_Year ≈ Issue_Year + Duration
```

```mermaid
flowchart LR
    subgraph Time["時間維度混淆"]
        A["Age Effect<br/>(生物老化)"]
        P["Period Effect<br/>(2012-2019醫療進步)"]
        C["Cohort Effect<br/>(Issue Year 世代差異)"]
    end
    
    A <-.-> P
    P <-.-> C
    C <-.-> A
    
    Note["⚠️ 三者線性相依<br/>無法完全識別"]
```

---

## 4. Selection 機制

```mermaid
flowchart TD
    subgraph S1["核保選擇"]
        Apply["申請投保"] --> UW["核保審查"]
        UW -->|通過| Issued["發行保單"]
        UW -->|拒絕| Declined["拒保 ❌"]
    end
    
    subgraph S2["存活選擇"]
        Issued --> InForce["持續有效"]
        Issued --> Lapse["失效/解約"]
        Issued --> Death2["死亡"]
    end
    
    subgraph S3["觀察窗口"]
        InForce --> Obs2012["2012-2019<br/>觀察期間"]
        Obs2012 --> Sample["進入樣本 ✓"]
    end
    
    Declined -.->|看不到| Hidden1["隱藏群體"]
    Lapse -.->|部分看不到| Hidden2["選擇性失效"]
```

---

## 5. 資料結構關鍵問題

| 問題 | 描述 | 影響 |
|------|------|------|
| **Left Truncation** | 2012 前發行的保單只有 later durations | Select period 不完整 |
| **Right Censoring** | 2019 後的死亡未觀察到 | 長 duration 樣本少 |
| **Survivorship Bias** | 只觀察到存活至觀察窗口的保單 | 低估早期死亡率 |
| **Aggregation** | 資料已彙總，非個別保單 | 無法做個體級分析 |
| **APC Confounding** | Age/Period/Cohort 線性相依 | 無法分離效應 |

---

## 6. 建議的結構性抽樣策略

### 6.1 Stratified Sampling

```python
# 按風險切面抽樣
strata = [
    ('Duration', [1, 5, 10, 15, 25]),  # Select vs Ultimate
    ('Attained_Age', [25, 40, 55, 70, 85]),  # Age groups
    ('Issue_Year', [1996, 2005, 2010, 2015]),  # Cohorts
    ('Smoker_Status', ['NS', 'S']),  # Risk factor
    ('Preferred_Class', [1, 2, 3, 4, 'NA'])  # Underwriting
]
```

### 6.2 高風險切面

1. **Duration 1-3**: Select period 核保剛過
2. **Duration ≥ 15**: Ultimate mortality
3. **Age > 70, Smoker**: 高死亡率群體
4. **Low Face Amount + Non-Preferred**: 反選擇風險
5. **Issue Year 2015+**: 新核保規則

### 6.3 邊界案例

- Duration = 1 且 Death > 0 (快進快出)
- Face Amount 極端值
- Preferred Class = 'U' (未知)
