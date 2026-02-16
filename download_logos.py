"""
School Logo Downloader for NFL Draft Scout Randomizer

This script helps you download college football team logos for use in the randomizer.
It uses the ESPN API to fetch team logos.
"""

import requests
import json
import urllib3
import re
from pathlib import Path

# Disable SSL warnings when verify=False is used
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def school_to_logo_filename(school_name):
    """Convert school name to logo file slug used by frontend"""
    slug = school_name.lower().strip()
    slug = re.sub(r'\s+', '-', slug)
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    return slug

def get_school_logos(schools):
    """
    Download logos for the given schools from ESPN
    
    Args:
        schools: List of school names
    """
    logos_dir = Path('static/logos')
    logos_dir.mkdir(parents=True, exist_ok=True)
    
    # ESPN College Football Teams API - try to get all teams with limit parameter
    espn_cfb_teams_url = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams?limit=1000"
    
    print("Fetching team data from ESPN...")
    try:
        response = requests.get(espn_cfb_teams_url, timeout=10, verify=False)
        response.raise_for_status()
        teams_data = response.json()
    except Exception as e:
        print(f"Error fetching teams data: {e}")
        return
    
    # Build a mapping of team names to logo URLs
    team_logos = {}
    if 'sports' in teams_data and len(teams_data['sports']) > 0:
        if 'leagues' in teams_data['sports'][0] and len(teams_data['sports'][0]['leagues']) > 0:
            teams = teams_data['sports'][0]['leagues'][0].get('teams', [])
            
            for team_entry in teams:
                team = team_entry.get('team', {})
                name = team.get('displayName', '')
                short_name = team.get('shortDisplayName', '')
                location = team.get('location', '')
                nickname = team.get('nickname', '')
                abbreviation = team.get('abbreviation', '')
                
                # Get logo URL
                logo_url = None
                if 'logos' in team and len(team['logos']) > 0:
                    logo_url = team['logos'][0].get('href', '')
                
                if logo_url:
                    # Add all possible name variations
                    if name:
                        team_logos[name.lower()] = logo_url
                    if short_name:
                        team_logos[short_name.lower()] = logo_url
                    if location:
                        team_logos[location.lower()] = logo_url
                    if nickname and nickname != short_name:
                        team_logos[nickname.lower()] = logo_url
                    if abbreviation:
                        team_logos[abbreviation.lower()] = logo_url
                    
                    # Also add just the school name (e.g., "Ohio State" from "Ohio State Buckeyes")
                    if name:
                        name_parts = name.split()
                        if len(name_parts) > 1:
                            shorter_name = ' '.join(name_parts[:-1])
                            team_logos[shorter_name.lower()] = logo_url
    
    # Get unique logo count (multiple names can point to same logo)
    unique_logos = len(set(team_logos.values()))
    print(f"Found {len(team_logos)} team name variations mapping to {unique_logos} unique logos")
    
    # Download logos for schools in our database
    downloaded = 0
    failed = []
    
    for school in schools:
        if not school:
            continue
            
        # Create filename
        filename = school_to_logo_filename(school)
        filepath = logos_dir / f"{filename}.png"
        
        # Skip if already exists
        if filepath.exists():
            print(f"Already have logo for {school}")
            continue
        
        # Try to find matching logo
        logo_url = None
        school_lower = school.lower().strip()
        
        # First try exact match
        if school_lower in team_logos:
            logo_url = team_logos[school_lower]
        else:
            # Try fuzzy matching - check if school name contains or is contained by any team name
            for team_name, url in team_logos.items():
                # Check if either name contains the other (handles "Florida St" vs "Florida State")
                if school_lower in team_name or team_name in school_lower:
                    logo_url = url
                    break
                
                # Also try with common words removed for better matching
                school_normalized = school_lower.replace('university', '').replace('state', '').replace('college', '').strip()
                team_normalized = team_name.replace('university', '').replace('state', '').replace('college', '').strip()
                
                if school_normalized and team_normalized:
                    if school_normalized in team_normalized or team_normalized in school_normalized:
                        logo_url = url
                        break
        
        if logo_url:
            try:
                # Download the logo
                logo_response = requests.get(logo_url, timeout=10, verify=False)
                logo_response.raise_for_status()
                
                with open(filepath, 'wb') as f:
                    f.write(logo_response.content)
                
                print(f"Downloaded logo for {school}")
                downloaded += 1
            except Exception as e:
                print(f"Failed to download logo for {school}: {e}")
                failed.append(school)
        else:
            print(f"No logo URL found for {school}")
            failed.append(school)
    
    print(f"\nDownloaded {downloaded} new logos")
    if failed:
        print(f"\nCould not find/download logos for {len(failed)} schools:")
        for school in failed[:10]: # Show first 10
            print(f" - {school}")
        if len(failed) > 10:
            print(f" ... and {len(failed) - 10} more")
        
        print(f"\nNote: Some schools may not be in ESPN's FBS/FCS database.")
        print(f"You can manually add logos by placing PNG files in static/logos/")
        example_filename = school_to_logo_filename(failed[0])
        print(f"For example, for '{failed[0]}', create: static/logos/{example_filename}.png")

def get_schools_from_database():
    """Get list of schools from the database"""
    try:
        from database import ScoutDatabase
        db = ScoutDatabase()
        players = db.get_all_players()
        schools = set()
        for player in players:
            if player.get('school'):
                schools.add(player['school'])
        return sorted(list(schools))
    except Exception as e:
        print(f"Error reading from database: {e}")
        return []

def get_schools_from_json():
    """Get list of schools from JSON file"""
    try:
        with open('nfl_big_board.json', 'r', encoding='utf-8') as f:
            players = json.load(f)
        schools = set()
        for player in players:
            if player.get('school'):
                schools.add(player['school'])
        return sorted(list(schools))
    except Exception as e:
        print(f"Error reading from JSON: {e}")
        return []

if __name__ == '__main__':
    print("=== School Logo Downloader ===\n")
    
    # Try to get schools from database first, then JSON
    schools = get_schools_from_database()
    if not schools:
        schools = get_schools_from_json()
    
    if not schools:
        print("No schools found! Make sure you've run webscraper.py first.")
    else:
        print(f"Found {len(schools)} schools to download logos for\n")
        get_school_logos(schools)
        print("\n Logo download complete!")
        print("\nNote: Some schools may not have matching logos in the ESPN database.")
        print("You can manually add logos by placing PNG files in the static/logos/ directory.")
        print("Filename format: school-name.png (e.g., 'ohio-state.png')")
