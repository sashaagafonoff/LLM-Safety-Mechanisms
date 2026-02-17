#!/usr/bin/env python3
"""Parse a data-review GitHub issue and extract the structured JSON payload."""

import json
import os
import re
import sys
import urllib.request


# Version 1 payloads (legacy form-based tool)
V1_REQUIRED_FIELDS = ["submission_type", "source_id", "technique_id", "evidence_text"]
V1_VALID_SUBMISSION_TYPES = {"review_existing", "add_new_tag"}
V1_VALID_ACTIONS = {"confirm", "adjust_confidence", "dispute", "add"}
V1_VALID_CONFIDENCE = {"High", "Medium", "Low"}

# Version 2 payloads (two-panel annotation tool)
V2_REQUIRED_FIELDS = ["action", "source_id", "technique_id", "evidence_text", "github_username"]
V2_VALID_ACTIONS = {"delete_tag", "link_evidence", "add_new_tag"}


def fetch_issue_body(issue_number: str) -> str:
    token = os.environ["GITHUB_TOKEN"]
    repo = os.environ.get("GITHUB_REPOSITORY", "sashaagafonoff/LLM-Safety-Mechanisms")
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    })
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())["body"]


def extract_json_block(body: str) -> dict:
    match = re.search(r"```json\s*\n(.*?)\n```", body, re.DOTALL)
    if not match:
        raise ValueError("No JSON code block found in issue body")
    return json.loads(match.group(1))


def validate(data: dict) -> None:
    version = data.get("version", 1)

    if version == 2:
        missing = [f for f in V2_REQUIRED_FIELDS if not data.get(f)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        if data["action"] not in V2_VALID_ACTIONS:
            raise ValueError(f"Invalid action: {data['action']}")
    else:
        missing = [f for f in V1_REQUIRED_FIELDS if not data.get(f)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        if data["submission_type"] not in V1_VALID_SUBMISSION_TYPES:
            raise ValueError(f"Invalid submission_type: {data['submission_type']}")
        action = data.get("action", "")
        if action and action not in V1_VALID_ACTIONS:
            raise ValueError(f"Invalid action: {action}")
        conf = data.get("new_confidence")
        if conf and conf not in V1_VALID_CONFIDENCE:
            raise ValueError(f"Invalid confidence: {conf}")


def write_output(key: str, value: str) -> None:
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a", encoding="utf-8") as f:
            # Multi-line safe output
            delimiter = "EOF_DELIM"
            f.write(f"{key}<<{delimiter}\n{value}\n{delimiter}\n")
    else:
        print(f"{key}={value}")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: parse_review_issue.py <issue_number>", file=sys.stderr)
        return 1

    issue_number = sys.argv[1]
    try:
        body = fetch_issue_body(issue_number)
        data = extract_json_block(body)
        validate(data)
        write_output("submission_json", json.dumps(data))
        print(f"Parsed {data['submission_type']} for {data['source_id']} / {data['technique_id']}")
        return 0
    except Exception as e:
        write_output("error", str(e))
        print(f"::error::Failed to parse issue: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
