"""GitHub PR reviewer tool."""

from typing import Dict, Any
from github import Github
from loguru import logger


class PRReviewer:
    """Reviews GitHub pull requests."""

    def __init__(self, auth_manager):
        """Initialize PR reviewer.

        Args:
            auth_manager: Authentication manager instance
        """
        self.auth_manager = auth_manager
        self.token = auth_manager.get_token("github")
        if self.token:
            self.github = Github(self.token)
        else:
            self.github = None

    async def review_pr(self, repo: str, pr_number: int) -> Dict[str, Any]:
        """Review a pull request.

        Args:
            repo: Repository (owner/name)
            pr_number: Pull request number

        Returns:
            Review details and recommendations
        """
        try:
            if not self.github:
                return {"error": "GitHub token not configured"}

            repo_obj = self.github.get_repo(repo)
            pr = repo_obj.get_pull(pr_number)

            # Collect PR information
            review_data = {
                "pr_number": pr_number,
                "title": pr.title,
                "author": pr.user.login,
                "state": pr.state,
                "additions": pr.additions,
                "deletions": pr.deletions,
                "changed_files": pr.changed_files,
                "commits": pr.commits,
                "labels": [label.name for label in pr.labels],
                "description": pr.body or "",
            }

            # Get files changed
            files = [
                {
                    "filename": file.filename,
                    "changes": file.changes,
                    "additions": file.additions,
                    "deletions": file.deletions,
                }
                for file in pr.get_files()
            ]

            review_data["files"] = files

            # Get commits
            commits = [
                {
                    "sha": commit.commit.sha[:8],
                    "message": commit.commit.message.split("\n")[0],
                    "author": commit.commit.author.name,
                }
                for commit in pr.get_commits()
            ]

            review_data["commits_list"] = commits

            # Get existing reviews
            reviews = [
                {
                    "author": review.user.login,
                    "state": review.state,
                    "body": review.body,
                }
                for review in pr.get_reviews()
            ]

            review_data["reviews"] = reviews

            logger.info(f"Reviewed PR {repo}#{pr_number}")
            return review_data

        except Exception as e:
            logger.error(f"Error reviewing PR: {e}")
            return {"error": str(e)}

    async def request_changes(
        self, repo: str, pr_number: int, comment: str
    ) -> Dict[str, Any]:
        """Request changes on a PR.

        Args:
            repo: Repository (owner/name)
            pr_number: Pull request number
            comment: Review comment

        Returns:
            Review submission result
        """
        try:
            if not self.github:
                return {"error": "GitHub token not configured"}

            repo_obj = self.github.get_repo(repo)
            pr = repo_obj.get_pull(pr_number)

            # Create review with requested changes
            review = pr.create_review(
                body=comment,
                event="REQUEST_CHANGES",
            )

            logger.info(f"Requested changes on PR {repo}#{pr_number}")
            return {
                "status": "changes_requested",
                "review_id": review.id,
                "comment": comment,
            }

        except Exception as e:
            logger.error(f"Error requesting changes: {e}")
            return {"error": str(e)}

    async def approve_pr(
        self, repo: str, pr_number: int, comment: str = ""
    ) -> Dict[str, Any]:
        """Approve a pull request.

        Args:
            repo: Repository (owner/name)
            pr_number: Pull request number
            comment: Optional approval comment

        Returns:
            Approval result
        """
        try:
            if not self.github:
                return {"error": "GitHub token not configured"}

            repo_obj = self.github.get_repo(repo)
            pr = repo_obj.get_pull(pr_number)

            # Create approval review
            review = pr.create_review(
                body=comment or "Looks good to me!",
                event="APPROVE",
            )

            logger.info(f"Approved PR {repo}#{pr_number}")
            return {
                "status": "approved",
                "review_id": review.id,
                "comment": comment,
            }

        except Exception as e:
            logger.error(f"Error approving PR: {e}")
            return {"error": str(e)}
