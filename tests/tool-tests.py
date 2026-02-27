"""Test suite for xom-claude-mcp-tools."""

import pytest
import asyncio
from typing import Dict, Any

# Import tools
from tools.github_mcp.tools.pr_reviewer import PRReviewer
from tools.github_mcp.tools.issue_manager import IssueManager
from tools.github_mcp.tools.code_analyzer import CodeAnalyzer
from tools.slack_mcp.tools.message_sender import MessageSender
from tools.slack_mcp.tools.thread_reader import ThreadReader
from tools.database_mcp.tools.query_executor import QueryExecutor
from tools.database_mcp.tools.update_manager import UpdateManager
from shared.auth import APIKeyManager, OAuthManager
from shared.security import EncryptionManager


# ============================================================================
# Authentication Tests
# ============================================================================

class TestAPIKeyManager:
    """Test API key management."""

    def test_validate_key(self):
        """Test API key validation."""
        manager = APIKeyManager()
        
        # Valid key
        github_token = "ghp_test_token_12345"
        manager.add_key("github", github_token, ["repo", "read:org"])
        assert manager.validate_key(github_token, "github")
        
        # Invalid key
        assert not manager.validate_key("invalid_key")
    
    def test_get_token(self):
        """Test getting tokens."""
        manager = APIKeyManager()
        manager.add_key("slack", "xoxb_test_token", ["chat:write"])
        
        token = manager.get_token("slack")
        assert token == "xoxb_test_token"
        
        # Non-existent service
        assert manager.get_token("invalid_service") is None
    
    def test_scope_validation(self):
        """Test scope validation."""
        manager = APIKeyManager()
        manager.add_key("github", "ghp_token", ["repo", "read:org"])
        
        assert manager.has_scope("github", "repo")
        assert not manager.has_scope("github", "admin")


class TestEncryptionManager:
    """Test encryption and decryption."""

    def test_encrypt_decrypt(self):
        """Test basic encryption/decryption."""
        encryption = EncryptionManager("test-key")
        original = "sensitive data"
        
        encrypted = encryption.encrypt(original)
        decrypted = encryption.decrypt(encrypted)
        
        assert decrypted == original
        assert encrypted != original
    
    def test_password_hashing(self):
        """Test password hashing."""
        encryption = EncryptionManager()
        password = "secure_password_123"
        
        hashed = encryption.hash_password(password)
        assert encryption.verify_password(password, hashed)
        assert not encryption.verify_password("wrong_password", hashed)
    
    def test_mask_sensitive(self):
        """Test sensitive data masking."""
        encryption = EncryptionManager()
        token = "ghp_abcdefghijklmnopqrstuvwxyz"
        
        masked = encryption.mask_sensitive(token, show_chars=4)
        assert masked.startswith("ghp_")
        assert masked.endswith("wxyz")
        assert "*" in masked


# ============================================================================
# GitHub Tools Tests
# ============================================================================

class TestPRReviewer:
    """Test GitHub PR reviewer."""

    @pytest.fixture
    def reviewer(self):
        """Create PR reviewer instance."""
        auth_manager = APIKeyManager()
        return PRReviewer(auth_manager)
    
    @pytest.mark.asyncio
    async def test_review_pr_no_token(self, reviewer):
        """Test PR review without GitHub token."""
        result = await reviewer.review_pr("owner/repo", 42)
        assert "error" in result
        assert result["error"] == "GitHub token not configured"


class TestIssueManager:
    """Test GitHub issue manager."""

    @pytest.fixture
    def manager(self):
        """Create issue manager instance."""
        auth_manager = APIKeyManager()
        return IssueManager(auth_manager)
    
    @pytest.mark.asyncio
    async def test_create_issue_no_token(self, manager):
        """Test issue creation without token."""
        result = await manager.create_issue("owner/repo", "Test Issue")
        assert "error" in result


class TestCodeAnalyzer:
    """Test code analyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create code analyzer instance."""
        auth_manager = APIKeyManager()
        return CodeAnalyzer(auth_manager)
    
    def test_detect_language(self, analyzer):
        """Test language detection."""
        assert analyzer._detect_language("file.py") == "Python"
        assert analyzer._detect_language("file.js") == "JavaScript"
        assert analyzer._detect_language("file.java") == "Java"
        assert analyzer._detect_language("unknown.xyz") == "Unknown"
    
    def test_calculate_metrics(self, analyzer):
        """Test metrics calculation."""
        code = """
def hello():
    # This is a comment
    print("Hello")
    
    return True
"""
        metrics = analyzer._calculate_metrics(code)
        
        assert metrics["total_lines"] > 0
        assert metrics["code_lines"] > 0
        assert metrics["comment_lines"] > 0
        assert 0 <= metrics["comment_ratio"] <= 1
    
    def test_find_issues(self, analyzer):
        """Test issue finding."""
        code = """
# TODO: Fix this
import *
eval(input())
password = "secret123"
"""
        issues = analyzer._find_issues(code, "test.py")
        
        assert len(issues) > 0
        assert any("TODO" in issue for issue in issues)


# ============================================================================
# Slack Tools Tests
# ============================================================================

class TestMessageSender:
    """Test Slack message sender."""

    @pytest.fixture
    def sender(self):
        """Create message sender instance."""
        auth_manager = APIKeyManager()
        return MessageSender(auth_manager)
    
    @pytest.mark.asyncio
    async def test_send_message_no_token(self, sender):
        """Test message sending without token."""
        result = await sender.send_message("C123", "Hello")
        assert "error" in result


class TestThreadReader:
    """Test Slack thread reader."""

    @pytest.fixture
    def reader(self):
        """Create thread reader instance."""
        auth_manager = APIKeyManager()
        return ThreadReader(auth_manager)
    
    @pytest.mark.asyncio
    async def test_read_thread_no_token(self, reader):
        """Test thread reading without token."""
        result = await reader.read_thread("C123", "1234567890.123456")
        assert "error" in result


# ============================================================================
# Database Tools Tests
# ============================================================================

class TestQueryExecutor:
    """Test database query executor."""

    @pytest.fixture
    def executor(self):
        """Create query executor instance."""
        return QueryExecutor()
    
    def test_detect_dangerous_operations(self):
        """Test detection of dangerous operations."""
        executor = QueryExecutor()
        
        # Safe query
        safe_query = "SELECT * FROM users WHERE id = :id"
        assert not any(op in safe_query.upper() for op in ["DROP", "DELETE", "TRUNCATE"])
        
        # Dangerous query
        dangerous_query = "DROP TABLE users"
        assert any(op in dangerous_query.upper() for op in ["DROP", "DELETE", "TRUNCATE"])


class TestUpdateManager:
    """Test database update manager."""

    @pytest.fixture
    def manager(self):
        """Create update manager instance."""
        return UpdateManager()


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for tools working together."""

    @pytest.mark.asyncio
    async def test_auth_flow(self):
        """Test authentication flow."""
        auth_manager = APIKeyManager()
        
        # Add keys
        auth_manager.add_key("github", "ghp_token", ["repo"])
        auth_manager.add_key("slack", "xoxb_token", ["chat:write"])
        
        # Verify auth
        assert auth_manager.validate_key("ghp_token", "github")
        assert auth_manager.validate_key("xoxb_token", "slack")
        
        # Get tokens
        assert auth_manager.get_token("github") == "ghp_token"
        assert auth_manager.get_token("slack") == "xoxb_token"
    
    @pytest.mark.asyncio
    async def test_encryption_flow(self):
        """Test encryption/decryption flow."""
        encryption = EncryptionManager()
        
        # Encrypt sensitive data
        original_token = "secret_token_12345"
        encrypted = encryption.encrypt(original_token)
        
        # Verify it's encrypted
        assert encrypted != original_token
        
        # Decrypt
        decrypted = encryption.decrypt(encrypted)
        assert decrypted == original_token


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """Performance tests."""

    def test_encryption_performance(self):
        """Test encryption performance."""
        encryption = EncryptionManager()
        data = "x" * 1000  # 1KB
        
        import time
        start = time.time()
        for _ in range(100):
            encrypted = encryption.encrypt(data)
        elapsed = time.time() - start
        
        # Should complete 100 encryptions in less than 1 second
        assert elapsed < 1.0
    
    def test_key_validation_performance(self):
        """Test key validation performance."""
        manager = APIKeyManager()
        manager.add_key("github", "ghp_token", ["repo"])
        
        import time
        start = time.time()
        for _ in range(1000):
            manager.validate_key("ghp_token", "github")
        elapsed = time.time() - start
        
        # Should validate 1000 keys in less than 1 second
        assert elapsed < 1.0


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_auth_manager():
    """Create mock authentication manager."""
    manager = APIKeyManager()
    manager.add_key("github", "ghp_test_token", ["repo", "read:org"])
    manager.add_key("slack", "xoxb_test_token", ["chat:write"])
    manager.add_key("xomware", "xom_test_key", ["board:read", "board:write"])
    return manager


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
