# Chandan's FP&A Job Hunting Agent

AI-powered job search system built with Google Agent Development Kit (ADK) for targeting finance/FP&A roles in Delhi NCR, India.

## Features

- **Job Discovery** - Web search (DuckDuckGo) for live FP&A/Finance job openings in Delhi NCR
- **Smart Scoring** - Evaluates jobs against profile (dealbreakers, skills, location, experience match)
- **Duplicate Detection** - Checks Google Sheets to avoid re-applying to same jobs
- **Application Tracking** - Auto-logs new applications to Google Sheets
- **Gmail Integration** - Scans for interview invites and updates application status

## Setup

### 1. Python Environment

```powershell
cd C:\Users\kunal\adk-workspace
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install requests pyyaml playwright duckduckgo-search google-auth-oauthlib google-api-python-client
python -m playwright install
```

### 2. Configure Profile

Edit `config/profile.yml` with your details:
- Target roles (FP&A Analyst, Finance Analyst, MIS Reporting, etc.)
- Target industries (Fintech, NBFC, Banking, etc.)
- Target locations (Delhi, Gurugram, Noida, etc.)
- Dealbreakers (CA requirement, night shifts, etc.)
- Your skills for matching

### 3. Update Your CV

Edit `cv.md` with your resume in markdown format. This is used for skill matching.

### 4. Google Sheets Integration (Optional)

For application tracking:

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project and enable Google Sheets API
3. Download OAuth credentials as `credentials.json`
4. Run `python agent.py` - browser will open for authentication
5. Token will be saved to `token.json` for future runs

### 5. Run the Agent

```powershell
cd C:\Users\kunal\adk-workspace\my_first_agent
.\..\.venv\Scripts\python.exe agent.py
```

## Project Structure

```
my_first_agent/
├── agent.py              # Main ADK agent + job search pipeline
├── tracker_agent.py      # Google Sheets + Gmail integration
├── cv.md                 # Your resume in markdown
├── .env                  # Environment variables
├── config/
│   └── profile.yml       # Job search criteria and target profile
├── core/
│   ├── evaluator.py      # Job scoring engine
│   └── scraper.py        # Web scraping with Playwright
├── credentials.json      # Google OAuth (add manually)
└── token.json            # Google auth token (auto-generated)
```

## How It Works

1. **Search** - Queries DuckDuckGo for jobs matching your target roles/locations
2. **Score** - Evaluates each job (0-100) based on title, location, industry, skills, experience
3. **Filter** - Skips jobs with dealbreakers (CA mandatory, night shifts, etc.)
4. **Dedup** - Checks Google Sheets to skip already-applied jobs
5. **Log** - Records new applications with date, company, title, URL, status

## Target Profile (Default)

- **Roles**: FP&A Analyst, Finance Analyst, MIS Reporting, R2R Analyst, Finance Associate
- **Industries**: Fintech, NBFC, Banking, Tech Consulting, Startups, Shared Services
- **Locations**: Delhi, Gurugram, Noida, Delhi NCR
- **Experience**: 1-4 years
- **Key Skills**: Excel (VBA, Macros, Pivots), Power BI, Tally, SAP, SQL, Financial Modelling

## Configuration

Edit `config/profile.yml`:

```yaml
candidate:
  name: "Your Name"
  experience_years: 2

target_criteria:
  roles:
    - "fp&a analyst"
    - "finance analyst"
    # Add more roles...
  industries:
    - "fintech"
    - "nbfc"
    # Add more industries...
  locations:
    - "delhi"
    - "gurugram"
    # Add more locations...
  skills:
    - "excel"
    - "power bi"
    # Add more skills...

dealbreakers:
  require_ca: true        # Set false if you have CA
  night_shifts: true      # Set false if you can do night shifts
  max_experience_limit: 4 # Don't show jobs requiring 5+ years
```

## Google Sheets Setup

Create a spreadsheet with this structure:

| Date | Company | Title | URL | Status | Follow-up |
|------|---------|-------|-----|--------|-----------|
| 2026-05-26 | Naukri | FP&A Analyst | link.com | Applied | 2026-05-28 |

Get the spreadsheet ID from the URL:
`https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`

Update `tracker_agent.py` line:
```python
SPREADSHEET_ID = 'YOUR_SPREADSHEET_ID_HERE'
```

## Troubleshooting

### No search results
- Check internet connection
- DuckDuckGo may be blocked - try VPN
- Update search queries in `agent.py`

### Google auth fails
- Delete `token.json` and re-run
- Ensure `credentials.json` is valid
- Check Google Sheets API is enabled in Cloud Console

### Import errors
- Ensure all packages installed: `pip install -r requirements.txt`
- Run `python -m playwright install` for browser automation

## License

MIT License - Use freely, modify as needed.

---

Built with Google ADK for Chandan's FP&A job search in India.