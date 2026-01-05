# Investor Operating System Agent

A refined, professional-grade evaluation framework for investment analysis that builds on 7 key investment questions and upgrades it into a repeatable investment protocol.

## Overview

This system automates the investment analysis workflow by:
1. Fetching financial data via Financial Modeling Prep (FMP) API
2. Calculating key investment metrics (profitability, growth, valuation, quality)
3. Scoring companies based on comprehensive investment criteria
4. Writing results to Google Sheets or Excel files
5. Storing analysis data in Google Drive or Google Cloud Storage

## Directory Structure

```
investor-agent/
  app/
    main.py                 # Entry point and orchestration logic
    config.py               # Configuration management
    fmp_client.py          # Financial Modeling Prep API client
    metrics.py             # Investment metrics calculator
    scoring.py             # Investment scoring engine
    writers/
      sheets_writer.py     # Google Sheets output writer
      excel_writer.py      # Excel file writer
    storage/
      drive_store.py       # Google Drive storage handler
      gcs_store.py         # Google Cloud Storage handler
  requirements.txt         # Python dependencies
  Dockerfile              # Container configuration
  cloudrun.yaml           # Cloud Run deployment config
```

## Features

### Investment Analysis Framework

The system evaluates companies based on 7 key questions:

1. **Is the business profitable and growing?**
   - Net margin, ROE, ROA, gross margin, operating margin
   - Revenue growth, earnings growth, CAGR

2. **Does it have a sustainable competitive advantage?**
   - High margins, strong cash flow generation
   - Quality metrics

3. **Is management effective and shareholder-friendly?**
   - ROE, capital allocation efficiency

4. **Is the valuation reasonable?**
   - P/E ratio, P/B ratio, Price-to-Sales, EV/EBITDA

5. **Is the financial position strong?**
   - Current ratio, quick ratio, interest coverage
   - Debt-to-equity, debt-to-EBITDA

6. **Are there catalysts for growth?**
   - Revenue and earnings growth trends

7. **What is the margin of safety?**
   - Overall scoring and valuation assessment

### Scoring System

- **Total Score (0-100)**: Weighted average of all categories
- **Category Scores**: Individual scores for each metric category
- **Recommendations**:
  - 80+: STRONG BUY - Excellent investment opportunity
  - 70-79: BUY - Good investment with solid fundamentals
  - 60-69: HOLD - Acceptable investment, monitor closely
  - 50-59: CAUTIOUS - Weak fundamentals
  - <50: AVOID - Poor investment metrics

## Installation

### Local Setup

```bash
cd investor-agent
pip install -r requirements.txt
```

### Docker Build

```bash
docker build -t investor-agent .
```

### Cloud Run Deployment

```bash
gcloud run services replace cloudrun.yaml --project=YOUR_PROJECT_ID
```

## Configuration

Set the following environment variables:

### Required
- `FMP_API_KEY`: Financial Modeling Prep API key

### Optional (for cloud features)
- `GCP_PROJECT_ID`: Google Cloud project ID
- `GCS_BUCKET_NAME`: GCS bucket for storing analysis files
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to GCP service account credentials
- `SHEETS_SPREADSHEET_ID`: Google Sheets spreadsheet ID
- `SHEETS_WORKSHEET_NAME`: Worksheet name (default: "Investment Analysis")
- `DRIVE_FOLDER_ID`: Google Drive folder ID for storage
- `OUTPUT_DIR`: Local output directory (default: "/tmp/investor-analysis")
- `LOG_LEVEL`: Logging level (default: "INFO")
- `SCORE_THRESHOLD_BUY`: Score threshold for BUY recommendation (default: 80)
- `SCORE_THRESHOLD_HOLD`: Score threshold for HOLD recommendation (default: 60)

## Usage

### Command Line

```bash
# Analyze a company and output to Google Sheets
python app/main.py AAPL sheets

# Analyze a company and output to Excel
python app/main.py MSFT excel
```

### Python API

```python
from config import Config
from fmp_client import FMPClient
from metrics import MetricsCalculator
from scoring import InvestmentScorer

# Initialize
config = Config()
fmp_client = FMPClient(config.fmp_api_key)

# Fetch data
company_data = fmp_client.get_company_data("AAPL")

# Calculate metrics
calculator = MetricsCalculator()
metrics = calculator.calculate(company_data)

# Score the investment
scorer = InvestmentScorer()
score = scorer.score(metrics)

print(f"Score: {score['total_score']}")
print(f"Recommendation: {scorer.get_recommendation(score)}")
```

## Dependencies

- **requests**: HTTP client for API calls
- **google-api-python-client**: Google Sheets and Drive APIs
- **google-cloud-storage**: Google Cloud Storage
- **openpyxl**: Excel file generation
- **python-dotenv**: Environment variable management

See `requirements.txt` for complete list.

## API Integration

This system uses the [Financial Modeling Prep (FMP) API](https://financialmodelingprep.com/) to fetch:
- Company profiles
- Income statements
- Balance sheets
- Cash flow statements
- Key financial metrics

Get your free API key at: https://financialmodelingprep.com/developer/docs/

## Output Formats

### Google Sheets
- Appends analysis results to a specified spreadsheet
- Includes summary, scores, strengths, and concerns

### Excel
- Creates formatted workbook with multiple sheets
- Summary sheet with key findings
- Detailed metrics sheet
- Category scores sheet

### Storage
- **Google Drive**: Stores JSON analysis files
- **Google Cloud Storage**: Stores Excel files and JSON data

## Architecture

The system follows a modular architecture:

1. **main.py**: Orchestrates the workflow
2. **config.py**: Manages configuration and environment variables
3. **fmp_client.py**: Handles all FMP API interactions
4. **metrics.py**: Calculates financial metrics from raw data
5. **scoring.py**: Applies investment framework to score companies
6. **writers/**: Output formatters for different destinations
7. **storage/**: Cloud storage integrations

## Error Handling

- Validates required configuration at startup
- Handles API errors gracefully
- Provides informative error messages
- Falls back to simple text format if Excel library unavailable

## Security

- API keys stored in environment variables (not in code)
- Secrets managed via Cloud Run secret manager
- Service account with minimal required permissions
- No sensitive data logged

## Performance

- Efficient API calls with session reuse
- Configurable auto-scaling on Cloud Run
- CPU and memory limits defined
- Request timeout: 5 minutes (configurable)

## Contributing

When adding new features:
1. Follow existing code structure
2. Add docstrings to all functions
3. Update this README
4. Test with multiple ticker symbols

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
1. Check the FMP API documentation
2. Verify environment variables are set correctly
3. Review Cloud Run logs if deployed

## Future Enhancements

Potential improvements:
- Batch analysis of multiple companies
- Historical trend analysis
- Comparative analysis across sectors
- Web dashboard for visualizations
- Real-time alerts for score changes
- Integration with additional data sources
