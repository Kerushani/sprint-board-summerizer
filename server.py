import requests
from requests.auth import HTTPBasicAuth
from collections import Counter
import json

# Email associated with your JIRA REST API token - https://id.atlassian.com/manage-profile/security/api-tokens
JIRA_EMAIL = " "

# Token can be made on https://id.atlassian.com/manage-profile/security/api-tokens
JIRA_API_TOKEN = ""

JIRA_DOMAIN = "xxxx.atlassian.net"

BOARD_ID = 642
SPRINT_ID = 6666
PREVIOUS_SPRINT_ID = SPRINT_ID - 1

BASE_URL = f"https://{JIRA_DOMAIN}"
AUTH = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
HEADERS = {"Accept": "application/json"}

unassigned_issues_summaries = []

def fetch_issues_from_sprint(sprint_id):
    url = f"{BASE_URL}/rest/agile/1.0/board/{BOARD_ID}/sprint/{sprint_id}/issue"
    issues = []
    start_at = 0

    while True:
        params = {"startAt": start_at, "maxResults": 50}
        response = requests.get(url, headers=HEADERS, auth=AUTH, params=params)
        response.raise_for_status()
        data = response.json()
        issues.extend(data["issues"])

        if start_at + 50 >= data["total"]:
            break
        start_at += 50

    return issues

def summarize_sprint(issues):
    summary = {
        "total_issues": 0,
        "completed_issues": 0,
        "unassigned_issues": 0,
        "unassigned_issues_summaries": [],
        "status_counts": Counter(),
        "story_points_total": 0,
        "story_points_completed": 0,
    }

    for issue in issues:
        fields = issue.get("fields", {})
        status = (fields.get("status") or {}).get("name", "Unknown")
        assignee = (fields.get("assignee") or {}).get("displayName", None)

        with open("sample-feilds.txt", "w") as f:
            f.write(json.dumps(issue, indent=2))

        # this feild can change based on where story points feild is stored on the application
        # replace with correct feild name
        story_points = fields.get("customfield_10003", 0)

        summary["total_issues"] += 1
        summary["status_counts"][status] += 1

        if assignee is None:
            summary["unassigned_issues"] += 1
            unassigned_issues_summaries.append(fields.get("summary") )
            with open("assignee-none.txt", "w") as f:
                f.write(json.dumps(fields, indent=2))

        if isinstance(story_points, (int, float)):
            summary["story_points_total"] += story_points
            if status.lower() in ["done", "closed", "resolved"]:
                summary["story_points_completed"] += story_points

        if status.lower() in ["done", "closed", "resolved"]:
            summary["completed_issues"] += 1

    return summary

def identify_carryover(current_issues, previous_issues):
    prev_keys = set(issue["key"] for issue in previous_issues)
    carried_over = [issue for issue in current_issues if issue["key"] in prev_keys]
    return carried_over

current_issues = fetch_issues_from_sprint(SPRINT_ID)

# writes JIRA REST API response into "sample-jira-rest-api-response.txt" file - useful to see what data you're getting back
with open("sample-jira-rest-api-response.txt", "w") as f:
    f.write(json.dumps(current_issues, indent=2))

previous_issues = fetch_issues_from_sprint(PREVIOUS_SPRINT_ID)

summary = summarize_sprint(current_issues)
carryover_issues = identify_carryover(current_issues, previous_issues)

sprint_summary_json = {
    "sprint_id": SPRINT_ID,
    "total_issues": summary["total_issues"],
    "story_points_total": summary["story_points_total"],
    "story_points_completed": summary["story_points_completed"],
    "completed_issues": summary["completed_issues"],
    "unassigned_issues": summary["unassigned_issues"],
    "unassigned_issues_summaries": unassigned_issues_summaries,
    "carryover_issues_count": len(carryover_issues),
    "status_breakdown": dict(summary["status_counts"]),
    "carryover_issues": [issue["key"] for issue in carryover_issues]
}

print(json.dumps(sprint_summary_json, indent=2))

with open("sample-feilds.txt", "w") as f:
    f.write(json.dumps(unassigned_issues_summaries, indent=2))