from jira import JIRA
import csv
import os
from hashlib import blake2b


# Define credentials file
credentials_file = "credentials.txt"

# Check for existence of credentials file
if not os.path.isfile("credentials.txt"):
    print("Credentials file not found! Generating...")
    email = input("Enter email: ")
    token = input("Enter token: ")
    password = input("Enter new password: ")
    repeat_pw = input("Repeat new password: ")
    if password != repeat_pw:
        print("Error! passwords do not match")
        exit(0)
    
    hash_obj = blake2b()
    hash_obj.update(password.encode())
    hashed_pw = hash_obj.hexdigest()
    with open(credentials_file, mode='w') as file:
        file.writelines((hashed_pw+"\n", email+"\n", token+"\n"))

# Load credentials from file
with open(credentials_file, mode='r') as file:
    password = input("Enter password: ")
    hash_obj = blake2b()
    hash_obj.update(password.encode())
    hashed_pw = hash_obj.hexdigest()
    if hashed_pw != file.readline().strip():
        print("Error! Password does not match!")
        exit(0)
    email = file.readline().strip()
    token = file.readline().strip()

# JIRA instance URL
jiraOptions = {'server': "https://team8-if.atlassian.net"}

jira = JIRA(options=jiraOptions, basic_auth=(email, token))

# Jira search query
jql_query = 'project = TESTBOARD'

# Perform Jira search
issues = jira.search_issues(jql_str=jql_query)

# Define CSV file path
csv_file = "jira_issues.csv"

# Open the CSV file in write mode
with open(csv_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    
    # Write the header row
    writer.writerow(["Key", "Summary", "Description", "Reporter"])
    
    # Iterate over the issues and write each row to the CSV file
    for issue in issues:
        key = issue.key
        summary = issue.fields.summary
        description = issue.fields.description
        reporter = issue.fields.reporter.displayName
        
        writer.writerow([key, summary, description, reporter])

print("Jira issues saved to", csv_file)
