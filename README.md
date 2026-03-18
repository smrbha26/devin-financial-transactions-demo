# Fraud Risk Scoring Pipeline

A rule-based fraud risk scoring pipeline that analyzes financial transactions, assigns risk scores (0–100), classifies them into risk categories, and generates a detailed report.

## Approach

The pipeline uses a **weighted rule-based scoring system** with six explainable signals:

| Signal | Weight | Description |
|--------|--------|-------------|
| High transaction amount | 25 | Transactions above $10,000 with scaling up to $200,000 |
| High-risk transaction type | 20 | CASH_OUT and TRANSFER types score higher |
| Sender balance zeroed | 15 | Account fully drained after the transaction |
| New destination account | 15 | Destination not previously seen in the dataset |
| Rapid transactions | 15 | Multiple transactions from the same originator |
| Amount-to-balance ratio | 10 | Transaction amount disproportionate to account balance |

Each signal contributes a weighted score, and the total is capped at 100. The final score determines the risk category:

| Category | Score Range |
|----------|-------------|
| **LOW** | score < 40 |
| **MEDIUM** | 40 ≤ score ≤ 70 |
| **HIGH** | score > 70 |

### Assumptions

- Input data follows the format of the provided `data/Example1.csv` (columns: `step`, `type`, `amount`, `nameOrig`, `oldbalanceOrg`, `newbalanceOrig`, `nameDest`, `oldbalanceDest`, `newbalanceDest`)
- Transactions are processed in order; "new destination" and "rapid transactions" are context-aware (depend on previously seen data)
- Rows with invalid or missing data are skipped with a warning
- Transaction IDs are generated sequentially (TXN-00001, TXN-00002, ...)

## Project Structure

```
├── data/
│   └── Example1.csv            # Sample input data
├── src/
│   ├── __init__.py
│   ├── scoring.py              # Risk scoring rules (modular, extensible)
│   ├── classification.py       # Risk category classification
│   ├── report.py               # CSV report generation
│   ├── validation.py           # Input validation
│   └── pipeline.py             # Main pipeline orchestration
├── tests/
│   ├── __init__.py
│   ├── test_scoring.py         # Unit tests for scoring logic
│   ├── test_classification.py  # Unit tests for classification + edge cases
│   └── test_pipeline.py        # Integration tests
├── output/
│   └── transaction_risk_report.csv  # Generated report
├── requirements.txt
└── README.md
```

## How to Run

### Prerequisites

- Python 3.10+
- Install dependencies:

```bash
pip install -r requirements.txt
```

### Run the Pipeline

```bash
# Default: reads data/Example1.csv, outputs to output/transaction_risk_report.csv
python -m src.pipeline

# Custom input/output paths
python -m src.pipeline -i path/to/input.csv -o path/to/output.csv

# Verbose (debug) logging
python -m src.pipeline -v
```

### Run Tests

```bash
python -m pytest tests/ -v
```

## Sample Input

```csv
step,type,amount,nameOrig,oldbalanceOrg,newbalanceOrig,nameDest,oldbalanceDest,newbalanceDest,isFraud,isFlaggedFraud
1,PAYMENT,9839.64,C1231006815,170136,160296.36,M1979787155,0,0,0,0
1,TRANSFER,181,C1305486145,181,0,C553264065,0,0,1,0
1,CASH_OUT,181,C840083671,181,0,C38997010,21182,0,1,0
```

## Sample Output

```csv
transaction_id,risk_score,risk_category,contributing_factors
TXN-00001,15.0,LOW,New/unseen destination account (M1979787155)
TXN-00003,56.0,MEDIUM,High-risk transaction type (TRANSFER); Sender balance zeroed after transaction; New/unseen destination account (C553264065); Transaction amount disproportionate to balance
TXN-00004,56.0,MEDIUM,High-risk transaction type (CASH_OUT); Sender balance zeroed after transaction; New/unseen destination account (C38997010); Transaction amount disproportionate to balance
TXN-00005,27.61,LOW,High transaction amount (11668.14); New/unseen destination account (M1230701703)
```
