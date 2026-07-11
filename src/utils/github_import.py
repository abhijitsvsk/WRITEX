import os
import io
import requests
import zipfile

def download_github_repo(url: str) -> io.BytesIO:
    """
    Downloads a GitHub repository as a ZIP file in-memory.
    Expects URLs like 'https://github.com/user/repo'.
    """
    url = url.strip()
    if not url.startswith("https://github.com/"):
        raise ValueError("Invalid GitHub URL. Must start with 'https://github.com/'")
    
    # Strip trailing slashes and .git
    url = url.rstrip('/')
    if url.endswith('.git'):
        url = url[:-4]
    
    parts = url.split('/')
    if len(parts) < 5:
        raise ValueError("Invalid GitHub URL format. Expected 'https://github.com/user/repo'")
    
    owner = parts[3]
    repo = parts[4]
    
    # Try main branch first, then master
    branches = ['main', 'master']
    
    for branch in branches:
        zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
        try:
            response = requests.get(zip_url, timeout=10)
            if response.status_code == 200:
                zip_file = io.BytesIO(response.content)
                zip_file.name = f"{repo}.zip" # Important for downstream validation
                return zip_file
        except requests.exceptions.RequestException:
            pass
            
    raise ValueError(f"Could not download repository. Ensure the repository is public and has a 'main' or 'master' branch.")
