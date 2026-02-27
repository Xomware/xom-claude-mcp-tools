"""GitHub issue manager tool."""

from typing import Dict, Any, Optional, List
from github import Github
from loguru import logger


class IssueManager:
    """Manages GitHub issues."""

    def __init__(self, auth_manager):
        """Initialize issue manager.

        Args:
            auth_manager: Authentication manager instance
        """
        self.auth_manager = auth_manager
        self.token = auth_manager.get_token("github")
        if self.token:
            self.github = Github(self.token)
        else:
            self.github = None

    async def create_issue(
        self,
        repo: str,
        title: str,
        body: str = "",
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a new issue.

        Args:
            repo: Repository (owner/name)
            title: Issue title
            body: Issue body/description
            labels: Optional list of labels
            assignees: Optional list of assignees

        Returns:
            Created issue details
        """
        try:
            if not self.github:
                return {"error": "GitHub token not configured"}

            repo_obj = self.github.get_repo(repo)

            # Create the issue
            issue = repo_obj.create_issue(
                title=title,
                body=body,
                labels=labels or [],
                assignees=assignees or [],
            )

            logger.info(f"Created issue {repo}#{issue.number}: {title}")
            return {
                "status": "created",
                "issue_number": issue.number,
                "url": issue.html_url,
                "title": issue.title,
            }

        except Exception as e:
            logger.error(f"Error creating issue: {e}")
            return {"error": str(e)}

    async def update_issue(
        self,
        repo: str,
        issue_number: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        state: Optional[str] = None,
        labels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Update an existing issue.

        Args:
            repo: Repository (owner/name)
            issue_number: Issue number
            title: Optional new title
            body: Optional new body
            state: Optional new state (open/closed)
            labels: Optional new labels

        Returns:
            Updated issue details
        """
        try:
            if not self.github:
                return {"error": "GitHub token not configured"}

            repo_obj = self.github.get_repo(repo)
            issue = repo_obj.get_issue(issue_number)

            # Update fields
            if title:
                issue.edit(title=title)
            if body:
                issue.edit(body=body)
            if state:
                issue.edit(state=state)
            if labels:
                issue.set_labels(*labels)

            logger.info(f"Updated issue {repo}#{issue_number}")
            return {
                "status": "updated",
                "issue_number": issue.number,
                "url": issue.html_url,
            }

        except Exception as e:
            logger.error(f"Error updating issue: {e}")
            return {"error": str(e)}

    async def add_comment(
        self, repo: str, issue_number: int, comment: str
    ) -> Dict[str, Any]:
        """Add a comment to an issue.

        Args:
            repo: Repository (owner/name)
            issue_number: Issue number
            comment: Comment text

        Returns:
            Comment creation result
        """
        try:
            if not self.github:
                return {"error": "GitHub token not configured"}

            repo_obj = self.github.get_repo(repo)
            issue = repo_obj.get_issue(issue_number)

            # Create comment
            comment_obj = issue.create_comment(comment)

            logger.info(f"Added comment to {repo}#{issue_number}")
            return {
                "status": "commented",
                "comment_id": comment_obj.id,
                "comment_url": comment_obj.html_url,
            }

        except Exception as e:
            logger.error(f"Error adding comment: {e}")
            return {"error": str(e)}

    async def assign_issue(
        self, repo: str, issue_number: int, assignees: List[str]
    ) -> Dict[str, Any]:
        """Assign issue to users.

        Args:
            repo: Repository (owner/name)
            issue_number: Issue number
            assignees: List of GitHub usernames

        Returns:
            Assignment result
        """
        try:
            if not self.github:
                return {"error": "GitHub token not configured"}

            repo_obj = self.github.get_repo(repo)
            issue = repo_obj.get_issue(issue_number)

            # Assign the issue
            issue.edit(assignees=assignees)

            logger.info(f"Assigned {repo}#{issue_number} to {assignees}")
            return {
                "status": "assigned",
                "issue_number": issue_number,
                "assignees": assignees,
            }

        except Exception as e:
            logger.error(f"Error assigning issue: {e}")
            return {"error": str(e)}

    async def list_issues(
        self, repo: str, state: str = "open", labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """List issues in a repository.

        Args:
            repo: Repository (owner/name)
            state: Issue state (open/closed/all)
            labels: Optional label filter

        Returns:
            List of issues
        """
        try:
            if not self.github:
                return {"error": "GitHub token not configured"}

            repo_obj = self.github.get_repo(repo)

            # Get issues
            issues = repo_obj.get_issues(state=state, labels=labels)

            issue_list = [
                {
                    "number": issue.number,
                    "title": issue.title,
                    "state": issue.state,
                    "author": issue.user.login,
                    "created_at": issue.created_at.isoformat(),
                    "updated_at": issue.updated_at.isoformat(),
                    "labels": [label.name for label in issue.labels],
                }
                for issue in issues
            ]

            logger.info(f"Listed {len(issue_list)} issues from {repo}")
            return {
                "status": "listed",
                "count": len(issue_list),
                "issues": issue_list,
            }

        except Exception as e:
            logger.error(f"Error listing issues: {e}")
            return {"error": str(e)}
