"""Security constraints for the agent."""

import ipaddress
import socket
from urllib.parse import urlparse

class SecurityViolation(Exception):
    """Raised when a security constraint is violated."""
    pass

class NavigationGuard:
    """Enforces network navigation security policies."""

    BLOCKED_NETWORKS = [
        ipaddress.ip_network("127.0.0.0/8"),      # Loopback
        ipaddress.ip_network("10.0.0.0/8"),       # Private Class A
        ipaddress.ip_network("172.16.0.0/12"),    # Private Class B
        ipaddress.ip_network("192.168.0.0/16"),   # Private Class C
        ipaddress.ip_network("169.254.169.254/32"), # Cloud Metadata
    ]

    ALLOWED_SCHEMES = {"http", "https"}

    @classmethod
    def validate_url(cls, url: str) -> None:
        """Validate that a URL is safe to navigate to.

        Args:
            url: The URL to check.

        Raises:
            SecurityViolation: If the URL is blocked or invalid.
        """
        parsed = urlparse(url)

        # 1. Check scheme
        if parsed.scheme not in cls.ALLOWED_SCHEMES:
            raise SecurityViolation(f"URL scheme '{parsed.scheme}' is not allowed. Only HTTP/HTTPS.")

        # 2. Check hostname resolution (SSRF protection)
        hostname = parsed.hostname
        if not hostname:
            raise SecurityViolation("URL must have a hostname.")

        try:
            # Resolve to IP to check against blocklist
            # Note: This is a point-in-time check. DNS rebinding attacks are still possible 
            # without a proxy, but this catches basic configuration errors.
            ip_addr_str = socket.gethostbyname(hostname)
            ip_addr = ipaddress.ip_address(ip_addr_str)
        except socket.gaierror:
             # If it doesn't resolve, it might be internal or invalid. 
             # For a beta tester, we assume public accessibility.
             raise SecurityViolation(f"Could not resolve hostname '{hostname}'.")

        # 3. Check against blocked networks
        for network in cls.BLOCKED_NETWORKS:
            if ip_addr in network:
                raise SecurityViolation(f"Access to IP {ip_addr} (local/private/metadata) is BLOCKED.")
