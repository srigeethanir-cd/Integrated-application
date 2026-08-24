"""End-to-end script to run Agent-2 on a sample story."""

import os
import sys
import json

# Ensure backend is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.agent2_story_generator.agent2 import Agent2StoryGenerator


def main():
    # Use a temporary project root inside workspace
    project_root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workspace", "e2e_test_project")
    os.makedirs(project_root, exist_ok=True)
    os.makedirs(os.path.join(project_root, "backend"), exist_ok=True)
    os.makedirs(os.path.join(project_root, "frontend"), exist_ok=True)
    os.makedirs(os.path.join(project_root, "database"), exist_ok=True)
    os.makedirs(os.path.join(project_root, "workspace"), exist_ok=True)
    os.makedirs(os.path.join(project_root, "metadata"), exist_ok=True)

    agent2 = Agent2StoryGenerator()

    stories = [
        {
            "story_key": "US-001",
            "title": "User Registration",
            "description": "Allow new users to register with email and password",
            "acceptance_criteria": {
                "criteria": [
                    "User can enter email and password",
                    "Email must be validated",
                    "Password is hashed before storage",
                    "Success response with user ID",
                ]
            },
        },
        {
            "story_key": "US-002",
            "title": "User Login",
            "description": "Allow existing users to login and receive JWT token",
            "acceptance_criteria": {
                "criteria": [
                    "User can login with email and password",
                    "JWT token issued on success",
                    "Invalid credentials return 401",
                ]
            },
        },
        {
            "story_key": "US-003",
            "title": "User Profile View",
            "description": "Authenticated users can view their profile information",
            "acceptance_criteria": {
                "criteria": [
                    "Profile endpoint requires valid JWT",
                    "Returns user name, email, created date",
                ]
            },
        },
    ]

    print("=" * 60)
    print("AGENT-2 END-TO-END EXECUTION")
    print("=" * 60)
    print(f"Project Root: {project_root}")
    print(f"Stories to process: {len(stories)}")
    print("=" * 60)

    results = []
    for story in stories:
        print(f"\n>>> Processing story: {story['story_key']} - {story['title']}")
        result = agent2.process_story(story=story, project_id="e2e_test_project")
        results.append(result)

        status = result.get("status", "unknown")
        merged = result.get("merged", False)
        print(f"    Status: {status}")
        print(f"    Merged: {merged}")
        if result.get("merged_files"):
            print(f"    Merged Files: {len(result['merged_files'])}")
            for f in result["merged_files"]:
                print(f"      - {f}")

    print("\n" + "=" * 60)
    print("EXECUTION SUMMARY")
    print("=" * 60)

    completed = sum(1 for r in results if r.get("status") == "completed")
    failed = sum(1 for r in results if r.get("status") == "validation_failed")
    print(f"Total Stories: {len(results)}")
    print(f"Completed:     {completed}")
    print(f"Failed:        {failed}")

    # Show project structure after merge
    print("\n" + "-" * 60)
    print("PROJECT STRUCTURE AFTER MERGE:")
    print("-" * 60)
    for root, dirs, files in os.walk(project_root):
        # Skip .merge_backup and .archive
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        level = root.replace(project_root, "").count(os.sep)
        indent = "  " * level
        print(f"{indent}{os.path.basename(root)}/")
        sub_indent = "  " * (level + 1)
        for f in files:
            print(f"{sub_indent}{f}")

    print("\n" + "=" * 60)
    print("AGENT-2 EXECUTION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
