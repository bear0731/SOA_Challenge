# SOA ILEC Mortality Prediction & Actuarial Report Generator

This project demonstrates a modern actuarial workflow combining **Machine Learning (LightGBM)** for mortality prediction with **Generative AI (Google Gemini)** for automated, ASOP-compliant reporting.

It uses the [SOA ILEC 2009-2019](https://www.soa.org/) dataset (approx. 45M records) to predict mortality rates and generate explainable actuarial insights.

---

## 🔬 Project Workflow

### 1. Exploratory Data Analysis (EDA)
We performed deep analysis to understand risk drivers before modeling.
- **Notebooks**: `code/ilec_comprehensive_eda.ipynb`, `code/eda_key_variables.ipynb`
- **Key Insights**:
    - **Non-linear Age Effect**: Mortality accelerates significantly after age 60.
    - **Duration "Risk Hump"**: Early durations show selection effects; durations >30y show higher uncertainty.
    - **Missing Data as Signal**: `Preferred_Class` NA values (32%) and `Smoker_Status` Unknown (8%) are distinct risk segments, not random errors.
    - **Product Mix**: Term insurance dominates (~46%), with UL/WL having distinct profiles.

### 2. Feature Engineering
Data preparation focused on preserving actuarial nuances.
- **Notebook**: `code/data_cleaning_lgbm.ipynb`
- **Techniques**:
    - **NA Handling**: Converted missing `Preferred_Class`, `Smoker_Status`, and `Post_Level_Ind` into explicit categories (e.g., "Unknown", "N/A") to capture structural risk.
    - **Encoding**: Label encoding for ordinal variables (Face Amount Band) and categorical variables (Plan Type).
    - **Feature Selection**: Selected 11 key features including `Attained_Age`, `Duration`, `Sex`, `Smoker_Status`, and `Insurance_Plan`.

### 3. Model Training (LightGBM)
We trained a Gradient Boosting Machine to predict mortality rates ($q_x$).
- **Notebook**: `code/lgbm_mortality_offset.ipynb`
- **Configuration**:
    - **Objective**: Regression (predicting `Death_Count / Exposure`).
    - **Weighting**: Weighted by `Policies_Exposed` to account for credibility.
    - **Calibration**: Achieved an overall A/E ratio of **0.9989**, indicating excellent calibration on the training set.

### 4. Validation & Interpretation
Ensuring the model is trustworthy and explainable.
- **Notebook**: `code/lgbm_model_validation.ipynb`
- **SHAP Analysis**: Used TreeExplainer to calculate exact contributions of each feature to the final prediction.
- **Metrics**: A/E Ratio, Relative Risk (RR), and Lift Charts.

### 5. LLM Report Generation (RAG-like System)
The core innovation is the **Automated Report Generator**.
- **Module**: `code/report_generator/`
- **Logic**:
    1.  **Knowledge Injection**: Loads statistical summaries, model contracts, and actuarial methodology into the System Prompt (~9,000 chars).
    2.  **Structured Generation**: Uses **Google Gemini 2.0 Flash** with Pydantic schemas to enforce valid JSON output.
    3.  **ASOP Compliance**: Follows ASOP 23 (Data), 25 (Credibility), 41 (Communication), and 56 (Modeling).
    4.  **Anomaly Detection**: "Spotlight" system identifies high-risk segments (e.g., predicted RR > 3.0x).

---

## 📂 File Structure

```
SOA/
├── README.md                          # This documentation
├── code/
│   ├── report_generator/              # MAIN PACKAGE
│   │   ├── demo_structured.py         # Entry point: Generates reports
│   │   ├── prompt_builder.py          # Builds full system prompt from knowledge base
│   │   ├── predictor.py               # LightGBM inference + SHAP
│   │   ├── llm.py                     # Google Gemini integration
│   │   ├── renderer.py                # Markdown/JSON report visualization
│   │   └── ...
│   ├── knowledge_generators/          # Scripts to create JSON knowledge base
│   ├── data_cleaning_lgbm.ipynb       # Feature engineering
│   ├── lgbm_mortality_offset.ipynb    # Model training
│   └── lgbm_model_validation.ipynb    # Validation
├── data/
│   ├── ilec_cleaned.parquet           # Processed ILEC data
│   └── reports/                       # Generated output (MD, JSON, PNG)
├── knowledge_base/                    # RAG Knowledge Source
│   ├── eda/                           # Statistical summaries
│   ├── calibration/                   # A/E ratios
│   ├── segments/                      # Coverage & Spotlight rules
│   └── methodology/                   # ASOP documentation
└── .env                               # API Keys
```

---

## 🚀 How to Run

### 1. Setup Environment
```bash
pip install pandas numpy lightgbm shap pydantic langchain-google-genai
```

### 2. Configure API Key
Create a `.env` file in the root directory:
```
GOOGLE_API_KEY=your_gemini_api_key_here
```

### 3. Run the Report Generator
The `demo_structured.py` script mimics a production environment. It loads the model, picks a sample (random or high-risk test), and generates a full report.

```bash
python code/report_generator/demo_structured.py
```

### 4. Toggle Test Mode
Open `code/report_generator/demo_structured.py`:
- Set `USE_TEST_DATA = True` to generate a **High-Risk Spotlight Report** (88yo Male Smoker).
- Set `USE_TEST_DATA = False` to run **Random Sampling** on the real dataset.

---

## 📝 Report Features

Each generated report (`data/reports/actuarial_report.md`) includes:
1.  **Executive Summary**: LLM-synthesized narrative.
2.  **Prediction Results**: Mortality Rate & Relative Risk (RR).
3.  **Evidence Charts**: SHAP Waterfall plot.
4.  **Segment Analysis**:
    - **Coverage**: Which demographic rule this policy falls into.
    - **Spotlight**: Warning if the policy is in a high-risk anomaly group.
5.  **Appendix A**: The **Full System Prompt** used for generation (Transparency).
