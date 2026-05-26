import yaml

def load_profile():
    """Load profile from YAML file."""
    try:
        with open("config/profile.yml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as exc:
        print(f"Warning: Could not load profile.yml: {exc}")
        return None

def score_job_fit(title: str, description: str, company: str) -> dict:
    """
    Score a job against the candidate profile.
    Returns dict with score (0-100), dealbreakers list, and matched_skills.
    """
    profile = load_profile()
    
    if not profile:
        # Fallback scoring if profile can't be loaded
        return {"score": 50, "dealbreakers": [], "matched_skills": []}
    
    score = 0
    dealbreakers_triggered = []
    matched_skills = []
    
    title_lower = title.lower()
    desc_lower = description.lower()
    criteria = profile["target_criteria"]
    dealbreakers = profile["dealbreakers"]
    
    # 1. Dealbreaker Scans
    if dealbreakers.get("require_ca", False):
        if "ca mandatory" in desc_lower or "must be a ca" in desc_lower or "chartered accountant mandatory" in desc_lower:
            dealbreakers_triggered.append("Mandatory CA Requirement")
            
    if dealbreakers.get("night_shifts", False):
        if ("night shift" in desc_lower or "us hours" in desc_lower or "us timing" in desc_lower):
            if "ameriprise" not in company.lower():
                dealbreakers_triggered.append("US/Night Shift Mandatory")
    
    # 2. Title Match (30 points)
    if any(role in title_lower for role in criteria.get("roles", [])):
        score += 30
    elif "finance" in title_lower or "analyst" in title_lower or "fp&a" in title_lower:
        score += 15
        
    # 3. Location Match (25 points)
    if any(loc in desc_lower or loc in title_lower for loc in criteria.get("locations", [])):
        score += 25
        
    # 4. Industry Match (25 points)
    if any(ind in desc_lower for ind in criteria.get("industries", [])):
        score += 25
    
    # 5. Skills Match (bonus)
    matched_skills = [skill for skill in criteria.get("skills", []) if skill in desc_lower]

    # 6. Experience Match (20 points)
    max_exp = dealbreakers.get("max_experience_limit", 4)
    if "5+" in desc_lower or "6+" in desc_lower or "7+" in desc_lower:
        if max_exp >= 5:
            score += 10  # Within acceptable range
        else:
            score += 5   # Slightly overqualified
    elif "1-3 years" in desc_lower or "1 year" in desc_lower or "2 years" in desc_lower:
        score += 20
    elif "fresher" in desc_lower or "entry level" in desc_lower:
        score += 15
    else:
        score += 10  # No specific requirement mentioned

    return {
        "score": min(score, 100),
        "dealbreakers": dealbreakers_triggered,
        "matched_skills": matched_skills
    }
