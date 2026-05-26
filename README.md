# FP&A Job Hunting Agent

AI-powered job search system built with Google Agent Development Kit (ADK) for targeting finance/FP&A roles in India.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Google ADK](https://img.shields.io/badge/Google-ADK-green)
![Playwright](https://img.shields.io/badge/Playwright-Web_Scraping-orange)
![DuckDuckGo](https://img.shields.io/badge/Search-DuckDuckGo-yellow)
![Google Sheets API](https://img.shields.io/badge/Google_Sheets-API-success)
![Gmail API](https://img.shields.io/badge/Gmail-API-red)

## Features

- **Job Discovery** - Web search (DuckDuckGo) for live job openings
- **Smart Scoring** - Evaluates jobs against profile (dealbreakers, skills, location, experience)
- **Duplicate Detection** - Checks Google Sheets to avoid re-applying
- **Application Tracking** - Auto-logs new applications to Google Sheets
- **Gmail Integration** - Scans for interview invites and updates status

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

```yaml
candidate:
  name: "Your Name"
  experience_years: 2

target_criteria:
  roles:
    - "fp&a analyst"
    - "finance analyst"
    # Add your target roles...
  industries:
    - "fintech"
    - "nbfc"
    # Add your target industries...
  locations:
    - "delhi"
    - "gurugram"
    # Add your target locations...
  skills:
    - "excel"
    - "power bi"
    # Add your skills...

dealbreakers:
  require_ca: false        # Set true if CA is mandatory for you
  night_shifts: true       # Set false if you can do night shifts
  max_experience_limit: 4   # Don't show jobs requiring more years
```

### 3. Update Your CV

Edit `cv.md` with your resume in markdown format.

### 4. Google Sheets Integration (Optional)

For application tracking:

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create project → Enable Google Sheets API
3. Download OAuth credentials as `credentials.json`
4. Run `python agent.py` - authenticate via browser popup

Update `tracker_agent.py` with your spreadsheet ID:
```python
SPREADSHEET_ID = 'YOUR_SPREADSHEET_ID'
```

### 5. Run

```powershell
cd C:\Users\kunal\adk-workspace\my_first_agent
.\..\.venv\Scripts\python.exe agent.py
```

## Project Structure

```
my_first_agent/
├── agent.py              # Main ADK agent + job search pipeline
├── tracker_agent.py      # Google Sheets + Gmail tracking
├── cv.md                 # Your resume in markdown
├── config/
│   └── profile.yml       # Job search criteria
├── core/
│   ├── evaluator.py      # Job scoring engine
│   └── scraper.py        # Web scraping with Playwright
├── credentials.json      # Google OAuth (add manually)
└── token.json            # Google auth token (auto-generated)
```

## How It Works

1. **Search** - Queries DuckDuckGo for jobs matching your target
2. **Score** - Evaluates each job (0-100) based on title, location, industry, skills
3. **Filter** - Skips jobs with dealbreakers (CA mandatory, night shifts, etc.)
4. **Dedup** - Checks Google Sheets to skip already-applied jobs
5. **Log** - Records new applications with date, company, title, URL, status

## Google Sheets Format

Create a spreadsheet with columns:
| Date | Company | Title | URL | Status | Follow-up |

Get spreadsheet ID from URL:
`https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`

## Troubleshooting

- **No search results**: Check internet connection, try VPN
- **Google auth fails**: Delete `token.json` and re-run
- **Import errors**: Run `pip install -r requirements.txt`
---

## 👤 Author
Built by **Chandan Tiwari** — [LinkedIn](https://www.linkedin.com/in/chandantiwari4/) · [GitHub](https://github.com/chandantiwariyt)
---

## License

MIT License
