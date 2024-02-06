import os
import requests
from datetime import datetime
import pytz
import re

def get_last_modified(username, repository, file_path, github_token=None):
    try:
        headers = {}
        
        if github_token:
            headers['Authorization'] = f'Bearer {github_token}'

        # Fetch the last commit information for the file using GitHub API
        api_url = f'https://api.github.com/repos/{username}/{repository}/commits?path={file_path}&per_page=1'
        response = requests.get(api_url, headers=headers)

        if response.status_code == 200:
            last_commit_data = response.json()[0]
            last_commit_date_str = last_commit_data['commit']['committer']['date']
            last_commit_date_utc = datetime.strptime(last_commit_date_str, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.UTC)
            return last_commit_date_utc
        else:
            print(f"GitHub API error: {response.status_code} - {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

def update_markdown_file(file_path, last_modified_date_str):
    try:
        # Read the content of the Markdown file
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Check if there is already a last modification date in the file
        pattern = re.compile(r'Last modified: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})')
        match = pattern.search(content)

        if match:
            # Update the existing last modification date
            content = pattern.sub(f'Last modified: {last_modified_date_str}', content)
        else:
            # Add a new last modification date section at the end of the file
            content += f'\n\nLast modified: {last_modified_date_str}'

        # Write the updated content back to the Markdown file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)

    except Exception as e:
        print(f"Error updating Markdown file: {e}")

def main():
    if 'GITHUB_ACTIONS' in os.environ:
        # Running in GitHub Actions environment
        github_token = os.getenv('GITHUB_TOKEN')
        username = os.getenv('GITHUB_REPOSITORY_OWNER')
        repository = os.getenv('GITHUB_REPOSITORY').split('/')[1]
    else:
        # Running locally, prompt for user input
        username = input("Enter your GitHub username: ")
        repository = input("Enter the GitHub repository name: ")
        github_token = None

    # List all Markdown files in the root directory
    markdown_files = [file for file in os.listdir() if file.endswith('.md')]

    # Iterate through each Markdown file and get the last modified date
    for file_name in markdown_files:
        file_path = file_name
        last_modified_date_utc = get_last_modified(username, repository, file_path, github_token)

        if last_modified_date_utc:
            # Convert UTC time to 'Europe/Paris' (UTC+1) and format without timezone information
            utc_plus_one = pytz.timezone('Europe/Paris')
            last_modified_date_tz = last_modified_date_utc.astimezone(utc_plus_one)
            last_modified_date_str = last_modified_date_tz.strftime('%Y-%m-%d %H:%M:%S')

            # Update the Markdown file with the last modified date
            update_markdown_file(file_path, last_modified_date_str)
            
            print(f"File: {file_name}, Last modified: {last_modified_date_str} (Updated in the file)")
        else:
            print(f"Unable to retrieve last modification date for file: {file_name}")

if __name__ == "__main__":
    main()
