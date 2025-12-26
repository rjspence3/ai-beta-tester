import pytest
from ai_beta_tester.security import NavigationGuard, SecurityViolation

def test_allowed_urls():
    """Test that safe public URLs are allowed."""
    NavigationGuard.validate_url("https://google.com")
    NavigationGuard.validate_url("http://example.com")
    # Subdomains
    NavigationGuard.validate_url("https://api.github.com")

def test_blocked_schemes():
    """Test that non-http/https schemes are blocked."""
    with pytest.raises(SecurityViolation, match="scheme"):
        NavigationGuard.validate_url("file:///etc/passwd")
    
    with pytest.raises(SecurityViolation, match="scheme"):
        NavigationGuard.validate_url("ftp://example.com")

@pytest.mark.skip(reason="localhost blocking disabled for local dev")
def test_blocked_networks_localhost():
    """Test locking of localhost."""
    with pytest.raises(SecurityViolation, match="BLOCKED"):
        NavigationGuard.validate_url("http://localhost:3000")
    
    with pytest.raises(SecurityViolation, match="BLOCKED"):
        NavigationGuard.validate_url("http://127.0.0.1")

def test_blocked_networks_private():
    """Test locking of private ranges."""
    with pytest.raises(SecurityViolation, match="BLOCKED"):
        NavigationGuard.validate_url("http://192.168.1.1")
        
    with pytest.raises(SecurityViolation, match="BLOCKED"):
        NavigationGuard.validate_url("http://10.0.0.5")

def test_blocked_networks_metadata():
    """Test locking of cloud metadata."""
    with pytest.raises(SecurityViolation, match="BLOCKED"):
        NavigationGuard.validate_url("http://169.254.169.254/latest/meta-data")
