from google.adk.agents.llm_agent import Agent
import html
import re
import requests
from urllib.parse import parse_qs, urlparse

try:
    from tracker_agent import log_new_application, check_already_applied, get_applications_list
except Exception as exc:
    log_new_application = None
    print(f"⚠️ Optional tracker_agent unavailable; application logging disabled. {exc}")

try:
    from duckduckgo_search import DDGS
except Exception:
    DDGS = None

# =====================================================================
# 1. LOAD PROFILE FROM YAML
# =====================================================================
try:
    import yaml
    with open("config/profile.yml", "r", encoding="utf-8") as f:
        PROFILE = yaml.safe_load(f)
    USER_PROFILE = PROFILE["target_criteria"]
    DEALBREAKERS = PROFILE["dealbreakers"]
    CANDIDATE = PROFILE["candidate"]
except Exception as exc:
    print(f"⚠️ Failed to load profile.yml: {exc}")
    print("Using hardcoded defaults...")
    USER_PROFILE = {
        "roles": ["fp&a analyst", "finance analyst", "finance associate", "mis reporting"],
        "industries": ["fintech", "nbfc", "technology consulting", "startups"],
        "locations": ["delhi", "gurugram", "noida", "ncr"],
        "skills": ["excel", "vba", "power bi", "financial modelling", "variance analysis", "budgeting"]
    }
    DEALBREAKERS = {"require_ca": True, "night_shifts": True, "max_experience_limit": 4}
    CANDIDATE = {"name": "Chandan Tiwari", "experience_years": 2}

def evaluate_and_score_job(title: str, description: str, company: str = "Unknown") -> dict:
    """
    Analyzes and scores a job description 0-100 based on the candidate profile.
    Flags dealbreakers automatically.
    """
    score = 0
    dealbreakers = []
    
    title_lower = title.lower()
    desc_lower = description.lower()
    
    # ---- 1. DEALBREAKER CHECKS ----
    if DEALBREAKERS.get("require_ca", False):
        if "ca mandatory" in desc_lower or "must be a ca" in desc_lower or "chartered accountant mandatory" in desc_lower:
            dealbreakers.append("Mandatory CA Qualification")
    
    if DEALBREAKERS.get("night_shifts", False):
        if ("night shift" in desc_lower or "us hours" in desc_lower or "us timing" in desc_lower):
            if "ameriprise" not in company.lower():
                dealbreakers.append("Mandatory US/Night Shifts")
    
    # ---- 2. TITLE MATCHING (Max 30 Points) ----
    if any(role in title_lower for role in USER_PROFILE.get("roles", [])):
        score += 30
    elif "finance" in title_lower or "accounts" in title_lower or "analyst" in title_lower or "fp&a" in title_lower:
        score += 15
        
    # ---- 3. LOCATION MATCHING (Max 25 Points) ----
    if any(loc in desc_lower or loc in title_lower for loc in USER_PROFILE.get("locations", [])):
        score += 25
        
    # ---- 4. INDUSTRY FIT (Max 25 Points) ----
    if any(ind in desc_lower for ind in USER_PROFILE.get("industries", [])):
        score += 25
        
    # ---- 5. SKILL OVERLAP (Bonus Points) ----
    matched_skills = [skill for skill in USER_PROFILE.get("skills", []) if skill in desc_lower]
    
    # ---- 6. EXPERIENCE APPROXIMATION (Max 20 Points) ----
    max_exp = DEALBREAKERS.get("max_experience_limit", 4)
    if f"0-{max_exp} years" in desc_lower or f"1-{max_exp} years" in desc_lower or f"{max_exp}+ years" in desc_lower:
        if "5+" in desc_lower or "6+" in desc_lower or "7+" in desc_lower or "8+" in desc_lower:
            score += 5  # Overqualified but still scoring
        else:
            score += 15
    elif "1-3 years" in desc_lower or "2 years" in desc_lower or "1 year" in desc_lower or "fresh" in desc_lower:
        score += 20
    elif "fresher" in desc_lower or "entry level" in desc_lower:
        score += 15
    else:
        score += 10  # No specific experience mentioned
        
    return {
        "score": min(score, 100),
        "dealbreakers": dealbreakers,
        "matched_skills": matched_skills
    }

# =====================================================================
# 2. BROWSING TOOL FUNCTION
# =====================================================================

def _extract_target_url(url: str) -> str:
    if url.startswith("//"):
        url = "https:" + url
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    if "uddg" in query:
        return html.unescape(query["uddg"][0])
    return url


def _parse_duckduckgo_html_search(html_text: str, max_results: int = 10) -> list:
    results = []
    title_pattern = re.compile(
        r'<a[^>]+class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
        re.I | re.S
    )
    snippet_pattern = re.compile(
        r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
        re.I | re.S
    )

    titles = title_pattern.findall(html_text)
    snippets = snippet_pattern.findall(html_text)

    for index, (href, title_html) in enumerate(titles):
        if len(results) >= max_results:
            break
        snippet_html = snippets[index] if index < len(snippets) else ""
        title = html.unescape(re.sub(r'<[^>]+>', '', title_html)).strip()
        snippet = html.unescape(re.sub(r'<[^>]+>', '', snippet_html)).strip()
        results.append({
            "title": title,
            "href": _extract_target_url(href),
            "body": snippet
        })

    if results:
        return results

    # Fallback to anchors only if snippet parsing fails
    anchor_pattern = re.compile(r'<a[^>]+class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.I | re.S)
    for href, title_html in anchor_pattern.findall(html_text):
        if len(results) >= max_results:
            break
        title = html.unescape(re.sub(r'<[^>]+>', '', title_html)).strip()
        results.append({
            "title": title,
            "href": _extract_target_url(href),
            "body": ""
        })

    return results


def _duckduckgo_html_search(query: str, max_results: int = 10) -> list:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    try:
        resp = requests.get("https://duckduckgo.com/html/", params={"q": query}, headers=headers, timeout=20)
        resp.raise_for_status()
        return _parse_duckduckgo_html_search(resp.text, max_results)
    except Exception as exc:
        print(f"DuckDuckGo HTML fallback search failed: {exc}")
        return []


def scout_live_opportunities(role_title: str, location: str) -> list:
    """
    Searches the live web for active job openings matching your profile parameters.
    Uses multiple search strategies with proper fallback.
    """
    print(f"🌐 Browsing the web for live '{role_title}' openings in '{location}'...")

    queries = [
        f"{role_title} jobs {location}",
        f"{role_title} hiring {location}",
        f"finance analyst jobs {location}",
        f"fp&a analyst jobs {location}",
        f"financial planning analyst {location}",
        f"mis reporting analyst {location}",
    ]

    discovered_jobs = []
    results = []
    search_success = False

    for query in queries:
        print(f"🔍 Searching with query: {query}")
        results = []  # Reset for each query
        
        try:
            # Try DDGS first
            if DDGS is not None:
                try:
                    with DDGS() as ddgs:
                        results = list(ddgs.text(query, max_results=10))
                    print(f"   DDGS returned {len(results)} results")
                except Exception as ddgs_err:
                    print(f"   DDGS failed: {ddgs_err}, trying HTML fallback...")
                    results = []
            
            # Fallback to HTML scraping if DDGS failed or returned empty
            if not results:
                results = _duckduckgo_html_search(query, max_results=10)
                print(f"   HTML fallback returned {len(results)} results")
                
        except Exception as exc:
            print(f"   Search error for '{query}': {exc}")
            # Try HTML fallback as last resort
            try:
                results = _duckduckgo_html_search(query, max_results=10)
                print(f"   Emergency fallback returned {len(results)} results")
            except Exception:
                results = []
                print(f"   Emergency fallback also failed")

        if results:
            print(f"   ✅ Found {len(results)} items for: {query}")
            search_success = True
            break

    if not search_success or not results:
        print("❌ No search results returned for any query.")
        return discovered_jobs

    # Process results - be less aggressive with filtering
    for result in results:
        title = result.get('title', '')
        url = result.get('href', 'No Link')
        snippet = result.get('body', '')

        # Skip only obvious non-job sites, but include LinkedIn/Indeed as fallback
        skip_patterns = ['youtube.com', 'twitter.com', 'facebook.com', 'instagram.com']
        if any(x in url.lower() for x in skip_patterns):
            continue

        if title and len(title) > 5:
            # Try to extract company name
            if " at " in title:
                company = title.split(" at ")[-1].strip()
                clean_title = title.split(" at ")[0].strip()
            elif " - " in title:
                company = title.split(" - ")[-1].strip()
                clean_title = title.split(" - ")[0].strip()
            else:
                company = "Target Company"
                clean_title = title.strip()
            
            # Skip if title looks like an ad or promotion
            if any(x in title.lower() for x in ['sponsored', 'ad - ', 'promoted']):
                continue
                
            discovered_jobs.append({
                "company": company,
                "title": clean_title,
                "url": url,
                "description": snippet
            })
            print(f"   📋 Added: {clean_title} at {company}")

    print(f"🌐 Total job leads discovered: {len(discovered_jobs)}")
    return discovered_jobs
# =====================================================================
# 3. DEFINE YOUR AGENTS
# =====================================================================
scout_agent = Agent(
    model='gemini-2.5-pro',
    name='job_scout_agent',
    description='Scours job boards and search engines to find live job postings matching Kunal\'s strict financial criteria.',
    instruction="""Identify active job postings that match the target list. Use evaluation filters to isolate high-scoring prospects.""",
    tools=[scout_live_opportunities]
)

# =====================================================================
# 4. PIPELINE ORCHESTRATION WITH AUTOMATED FILTERING
# =====================================================================
def run_job_hunting_pipeline():
    candidate_name = CANDIDATE.get("name", "Candidate")
    print(f"🚀 Initializing Job Hunting Pipeline for {candidate_name}...")
    print(f"   Experience: {CANDIDATE.get('experience_years', 'N/A')} years")
    print(f"   Target Locations: {', '.join(USER_PROFILE.get('locations', [])[:4])}")
    print()

    # Benchmark Evaluation: Run the sample B2B OTA Job Description you provided
    sample_jd_title = "B2B Accounts & Operations Specialist"
    sample_jd_text = """
    Manage complete accounting lifecycle for B2B OTA transactions. Handle day-to-day accounting functions, journal entries, ledger scrutiny.
    Maintain compliance with all statutory regulations including GST, TDS. 1-3 years of hands-on experience in B2B accounting, ideally in a tech-driven environment.
    """
    print("--- Testing Filter Against Sample B2B OTA Job ---")
    evaluation = evaluate_and_score_job(title=sample_jd_title, description=sample_jd_text, company="B2B OTA Startup")
    print(f"📋 Title: {sample_jd_title}")
    print(f"🎯 Fit Score: {evaluation['score']}/100")
    print(f"⚠️ Dealbreakers: {evaluation['dealbreakers'] if evaluation['dealbreakers'] else 'None'}")
    print(f"💡 Matched Skills: {evaluation['matched_skills']}")
    print()

    # Run live search sweep for primary targets
    print("--- Starting Live Job Search ---")
    live_leads = scout_live_opportunities(role_title="FP&A Analyst", location="Delhi NCR")
    
    if not live_leads:
        print("\n❌ No job leads discovered. Trying alternative search...")
        # Try alternative search terms
        live_leads = scout_live_opportunities(role_title="Finance Analyst", location="Gurugram")
        
    if not live_leads:
        print("❌ No matching open postings discovered. Tips:")
        print("   - Try expanding your target locations")
        print("   - Check your internet connection")
        print("   - Verify DuckDuckGo is accessible from your network")
        return
        
    print(f"\n📊 Evaluating {len(live_leads)} job leads...")
    strong_targets = []
    
    for lead in live_leads:
        analysis = evaluate_and_score_job(title=lead['title'], description=lead['description'], company=lead['company'])
        
        # FILTER: Only strong matches with no dealbreakers
        if analysis['score'] >= 40 and not analysis['dealbreakers']:
            strong_targets.append({
                **lead,
                'score': analysis['score'],
                'matched_skills': analysis['matched_skills']
            })
            print(f"🔥 Match: {lead['title']} at {lead['company']} (Score: {analysis['score']}/100)")
        else:
            reason = "dealbreaker" if analysis['dealbreakers'] else f"low score ({analysis['score']})"
            print(f"⏭️ Skipped: {lead['title']} - {reason}")
    
    print(f"\n📈 Summary: Found {len(strong_targets)} strong matches out of {len(live_leads)} leads")
    
    # Check for already-applied jobs
    applied_before = []
    new_matches = []
    
    for target in strong_targets:
        if check_already_applied(target['company'], target['title']):
            applied_before.append(target)
        else:
            new_matches.append(target)
    
    if applied_before:
        print(f"\n⚠️ {len(applied_before)} jobs already applied to (skipped)")
    
    if new_matches:
        print(f"\n✨ {len(new_matches)} NEW opportunities (not yet applied)")
        new_matches.sort(key=lambda x: x['score'], reverse=True)
        print("\n🏆 New Top Matches:")
        for i, target in enumerate(new_matches[:3], 1):
            print(f"   {i}. {target['title']} at {target['company']}")
            print(f"      Score: {target['score']}/100 | Skills: {target['matched_skills']}")
            print(f"      URL: {target['url']}")
        
        # Log new applications
        print("\n📝 Logging new applications...")
        for target in new_matches[:3]:
            print(f"📌 New Match: {target['title']} at {target['company']}")
            if log_new_application is not None:
                try:
                    log_new_application(
                        company=target['company'], 
                        title=target['title'], 
                        job_url=target['url']
                    )
                except Exception as exc:
                    print(f"   ⚠️ Could not log to tracker: {exc}")
        
        # Show top pick
        top = new_matches[0]
        print(f"\n📌 Top Pick: {top['title']} at {top['company']}")
        print(f"   Apply here: {top['url']}")
    else:
        print("\n🎉 You've already applied to all top matches!")
        print("   Check your Google Sheet for status updates.")

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--check-applications':
        # Standalone command to check applied jobs
        print("🔍 Checking your applied jobs...\n")
        try:
            from tracker_agent import get_applications_list
            get_applications_list()
        except Exception as exc:
            print(f"Error: {exc}")
    else:
        run_job_hunting_pipeline()