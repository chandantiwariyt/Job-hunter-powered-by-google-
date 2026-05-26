import os.path
from datetime import datetime, timedelta

# Google auth imports - wrapped in try/except for graceful degradation
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_AUTH_AVAILABLE = True
except ImportError as exc:
    GOOGLE_AUTH_AVAILABLE = False
    print(f"⚠️ Google auth libraries not available: {exc}")

# Updated SCOPES to include both Sheets and Gmail Read-Only
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/gmail.readonly'
]

SPREADSHEET_ID = '1XlYxQS5pTFNOnQgMsZ7w4xu76RAX08clj6_mnHeGysA' 

def get_google_credentials():
    if not GOOGLE_AUTH_AVAILABLE:
        raise Exception("Google auth libraries not installed")
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def log_new_application(company: str, title: str, job_url: str):
    """Log a new job application to Google Sheets."""
    if not GOOGLE_AUTH_AVAILABLE:
        raise Exception("Google auth libraries not installed")
    
    try:
        creds = get_google_credentials()
        sheets_service = build('sheets', 'v4', credentials=creds)
        
        today = datetime.now().strftime('%Y-%m-%d')
        follow_up = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
        
        row_data = [today, company, title, job_url, 'Applied', follow_up]
        body = {'values': [row_data]}
        
        sheets_service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range="Sheet1!A:F",
            valueInputOption="USER_ENTERED",
            body=body
        ).execute()
        print(f"   ✅ Logged: {title} @ {company}")
    except Exception as err:
        print(f"   ❌ Sheets Error: {err}")
        raise

def get_applications_list() -> list:
    """Fetch all logged applications from Google Sheets."""
    if not GOOGLE_AUTH_AVAILABLE:
        raise Exception("Google auth libraries not installed")
    
    creds = get_google_credentials()
    sheets_service = build('sheets', 'v4', credentials=creds)
    
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range="Sheet1!A:F"
    ).execute()
    
    rows = result.get('values', [])
    
    if not rows or len(rows) <= 1:
        print("No applications logged yet.")
        return []
    
    applications = []
    for row in rows[1:]:
        applications.append({
            "date": row[0] if len(row) > 0 else "",
            "company": row[1] if len(row) > 1 else "",
            "title": row[2] if len(row) > 2 else "",
            "url": row[3] if len(row) > 3 else "",
            "status": row[4] if len(row) > 4 else "Applied",
            "follow_up": row[5] if len(row) > 5 else ""
        })
    
    return applications

def check_already_applied(company: str, title: str) -> bool:
    """Check if you've already applied to this job."""
    try:
        applications = get_applications_list()
        if not applications:
            return False
        
        company_lower = company.lower().strip()
        title_lower = title.lower().strip()
        
        for app in applications:
            app_company = app['company'].lower().strip()
            app_title = app['title'].lower().strip()
            
            # Check for fuzzy match
            if (company_lower and app_company and 
                (company_lower in app_company or app_company in company_lower or
                 company_lower in app_title or app_title in company_lower)):
                print(f"   ⚠️ Already applied: {app['title']} @ {app['company']} (Status: {app['status']})")
                return True
            
            # Also check by title alone for exact matches
            if title_lower and app_title:
                if title_lower == app_title:
                    print(f"   ⚠️ Already applied: {app['title']} @ {app['company']} (Status: {app['status']})")
                    return True
        
        return False
    except Exception as exc:
        print(f"   Warning: Could not check applications: {exc}")
        return False

def print_applications():
    """Print all logged applications."""
    try:
        applications = get_applications_list()
        
        if not applications:
            print("No applications logged yet.")
            return
        
        print("\n📋 Your Applied Jobs:")
        print("-" * 80)
        
        for i, app in enumerate(applications, 1):
            print(f"{i}. {app['title']} @ {app['company']}")
            print(f"   Date: {app['date']} | Status: {app['status']}")
            print(f"   URL: {app['url']}")
            if app['follow_up']:
                print(f"   Follow-up: {app['follow_up']}")
            print()
        
        print(f"Total: {len(applications)} applications")
        
    except Exception as exc:
        print(f"Error: {exc}")

def scan_gmail_for_updates():
    """Scan Gmail for interview invitations and update sheet."""
    if not GOOGLE_AUTH_AVAILABLE:
        print("Gmail scanning disabled - auth libraries not available")
        return
        
    try:
        creds = get_google_credentials()
        gmail_service = build('gmail', 'v1', credentials=creds)
        sheets_service = build('sheets', 'v4', credentials=creds)
        
        print("Scanning Gmail for interview invitations...")
        # Search query looking for interview-related emails
        query = "subject:('interview' OR 'invitation to interview' OR 'schedule a time')"
        
        results = gmail_service.users().messages().list(userId='me', q=query, maxResults=10).execute()
        messages = results.get('messages', [])
        
        if not messages:
            print("No new interview emails found.")
            return

        # Pull down the current sheet entries
        sheet_data = sheets_service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range="Sheet1!A:F"
        ).execute()
        rows = sheet_data.get('values', [])

        print(f"Checking {len(messages)} recent emails against your tracking sheet...")
        updates = 0
        for msg in messages:
            msg_data = gmail_service.users().messages().get(userId='me', id=msg['id']).execute()
            snippet = msg_data.get('snippet', '').lower()
            
            # Look through your spreadsheet rows (skipping the header)
            for index, row in enumerate(rows[1:], start=2):
                company_name = row[1].lower() if len(row) > 1 else ""
                current_status = row[4] if len(row) > 4 else ""
                
                # If the email mentions the company name and you haven't updated it yet
                if company_name and company_name in snippet and current_status != 'Interviewing':
                    print(f"🎉 Match found! Updating status for {row[1]} to 'Interviewing'...")
                    
                    # Update column E (Status) for this specific row
                    sheets_service.spreadsheets().values().update(
                        spreadsheetId=SPREADSHEET_ID,
                        range=f"Sheet1!E{index}",
                        valueInputOption="USER_ENTERED",
                        body={'values': [['Interviewing']]}
                    ).execute()
                    updates += 1
                    
        if updates:
            print(f"Updated {updates} application(s) to 'Interviewing'")
        else:
            print("No status updates needed.")
                    
    except Exception as err:
        print(f"Automation Error: {err}")