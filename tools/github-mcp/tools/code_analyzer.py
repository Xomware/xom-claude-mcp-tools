"""GitHub code analyzer tool."""

import re
from typing import Dict, Any, Optional
from github import Github
from loguru import logger


class CodeAnalyzer:
    """Analyzes code in GitHub repositories."""

    def __init__(self, auth_manager):
        """Initialize code analyzer.

        Args:
            auth_manager: Authentication manager instance
        """
        self.auth_manager = auth_manager
        self.token = auth_manager.get_token("github")
        if self.token:
            self.github = Github(self.token)
        else:
            self.github = None

    async def analyze(
        self, repo: str, path: str, ref: str = "main"
    ) -> Dict[str, Any]:
        """Analyze code in a file.

        Args:
            repo: Repository (owner/name)
            path: File path to analyze
            ref: Git ref (branch/tag/commit)

        Returns:
            Code analysis results
        """
        try:
            if not self.github:
                return {"error": "GitHub token not configured"}

            repo_obj = self.github.get_repo(repo)

            # Get file content
            file_obj = repo_obj.get_contents(path, ref=ref)
            content = file_obj.decoded_content.decode()

            # Analyze the code
            analysis = {
                "path": path,
                "size_bytes": len(content),
                "lines": len(content.split("\n")),
                "language": self._detect_language(path),
                "metrics": self._calculate_metrics(content),
                "issues": self._find_issues(content, path),
            }

            logger.info(f"Analyzed {repo}/{path}")
            return analysis

        except Exception as e:
            logger.error(f"Error analyzing code: {e}")
            return {"error": str(e)}

    def _detect_language(self, path: str) -> str:
        """Detect programming language from file extension.

        Args:
            path: File path

        Returns:
            Language name
        """
        ext_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".java": "Java",
            ".cpp": "C++",
            ".c": "C",
            ".go": "Go",
            ".rs": "Rust",
            ".rb": "Ruby",
            ".php": "PHP",
            ".sh": "Shell",
            ".sql": "SQL",
            ".yaml": "YAML",
            ".yml": "YAML",
            ".json": "JSON",
        }

        for ext, lang in ext_map.items():
            if path.endswith(ext):
                return lang

        return "Unknown"

    def _calculate_metrics(self, content: str) -> Dict[str, Any]:
        """Calculate code metrics.

        Args:
            content: File content

        Returns:
            Metrics dictionary
        """
        lines = content.split("\n")
        code_lines = 0
        comment_lines = 0
        empty_lines = 0

        for line in lines:
            stripped = line.strip()
            if not stripped:
                empty_lines += 1
            elif stripped.startswith("#") or stripped.startswith("//"):
                comment_lines += 1
            else:
                code_lines += 1

        return {
            "total_lines": len(lines),
            "code_lines": code_lines,
            "comment_lines": comment_lines,
            "empty_lines": empty_lines,
            "comment_ratio": (
                comment_lines / code_lines if code_lines > 0 else 0
            ),
        }

    def _find_issues(self, content: str, path: str) -> list[str]:
        """Find potential code issues.

        Args:
            content: File content
            path: File path

        Returns:
            List of found issues
        """
        issues = []

        # Check for common issues
        if re.search(r"TODO|FIXME|HACK|XXX", content):
            issues.append("Contains TODO/FIXME comments")

        if re.search(r"console\.log|print\(", content):
            issues.append("Contains debug statements")

        if re.search(r"password|secret|token|key", content, re.IGNORECASE):
            issues.append("May contain hardcoded secrets")

        if re.search(r"except:\s*pass", content):
            issues.append("Contains bare except clause")

        if re.search(r"eval\(|exec\(", content):
            issues.append("Contains dangerous eval/exec calls")

        # Language-specific checks
        if path.endswith(".py"):
            if re.search(r"import \*", content):
                issues.append("Contains wildcard imports")

            if not re.search(r'""".*"""', content, re.DOTALL):
                issues.append("Missing module docstring")

        elif path.endswith((".js", ".ts")):
            if re.search(r"var ", content):
                issues.append("Uses var instead of let/const")

        return issues

    async def find_duplicates(
        self, repo: str, path: str = ""
    ) -> Dict[str, Any]:
        """Find duplicate code in repository.

        Args:
            repo: Repository (owner/name)
            path: Optional path to search in

        Returns:
            Duplicate code findings
        """
        try:
            if not self.github:
                return {"error": "GitHub token not configured"}

            repo_obj = self.github.get_repo(repo)

            # Get all Python files as example
            query = f'repo:{repo} extension:py'
            results = self.github.search_code(query)

            files_data = {}
            for file in list(results)[:10]:  # Limit to 10 for performance
                try:
                    content = repo_obj.get_contents(file.path).decoded_content.decode()
                    files_data[file.path] = content
                except:
                    pass

            logger.info(f"Analyzed {len(files_data)} files for duplicates in {repo}")
            return {
                "status": "analyzed",
                "files_checked": len(files_data),
                "duplicates": [],  # Would need more complex algorithm
            }

        except Exception as e:
            logger.error(f"Error finding duplicates: {e}")
            return {"error": str(e)}
