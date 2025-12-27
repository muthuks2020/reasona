# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in Reasona, please report it responsibly.

### How to Report

**DO NOT** create a public GitHub issue for security vulnerabilities.

Instead, please email security concerns to: **security@reasona.dev**

Include the following information:

1. **Description** of the vulnerability
2. **Steps to reproduce** the issue
3. **Potential impact** assessment
4. **Suggested fix** (if you have one)
5. **Your contact information** for follow-up

### What to Expect

- **Acknowledgment**: Within 48 hours of your report
- **Initial Assessment**: Within 5 business days
- **Resolution Timeline**: Based on severity, typically 30-90 days
- **Credit**: We'll credit you in the release notes (unless you prefer anonymity)

### Severity Levels

| Level    | Description                                    | Response Time |
| -------- | ---------------------------------------------- | ------------- |
| Critical | Remote code execution, data breach             | 24-48 hours   |
| High     | Authentication bypass, sensitive data exposure | 3-5 days      |
| Medium   | Limited impact vulnerabilities                 | 7-14 days     |
| Low      | Minor issues, theoretical attacks              | 30 days       |

## Security Best Practices

When using Reasona, follow these security guidelines:

### API Key Management

```python
# ✅ Good: Use environment variables
import os
from reasona import Conductor

conductor = Conductor(
    model="openai/gpt-4o"
    # API key loaded from OPENAI_API_KEY env var
)

# ❌ Bad: Hardcoded API keys
conductor = Conductor(
    model="openai/gpt-4o",
    api_key="sk-..."  # Never do this!
)
```

### Tool Security

```python
from reasona.tools import ShellCommand

# ⚠️ ShellCommand executes arbitrary commands
# Only use in trusted environments
shell = ShellCommand()

# Consider restricting commands
shell = ShellCommand(
    allowed_commands=["ls", "cat", "grep"],
    timeout=30
)
```

### Input Validation

```python
from reasona import Conductor

# Validate user input before passing to agents
def process_user_input(user_input: str) -> str:
    # Sanitize input
    sanitized = user_input.strip()[:10000]  # Limit length
    
    # Validate content
    if contains_injection(sanitized):
        raise ValueError("Invalid input detected")
    
    return sanitized
```

### Network Security

```python
from reasona.mcp import HyperMCP

mcp = HyperMCP(name="secure-server")

# Enable authentication
@mcp.tool(requires_auth=True)
async def sensitive_operation(data: str) -> dict:
    token = get_token()
    if not validate_token(token):
        raise PermissionError("Invalid token")
    # ... perform operation
```

### Logging and Monitoring

```python
import logging
from reasona import Conductor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Monitor agent activity
conductor = Conductor(
    model="openai/gpt-4o",
    callbacks=[
        LoggingCallback(),
        AuditCallback()
    ]
)
```

## Known Security Considerations

### LLM Prompt Injection

AI agents may be vulnerable to prompt injection attacks. Mitigations:

- Validate and sanitize all user inputs
- Use system prompts to establish boundaries
- Monitor for unexpected behavior
- Implement output validation

### Tool Execution

Some built-in tools execute system operations:

- `ShellCommand`: Executes shell commands
- `FileWriter`: Writes to filesystem
- `HttpRequest`: Makes network requests

**Recommendation**: Only enable these tools in trusted environments.

### Data Privacy

Agent conversations may contain sensitive data:

- Implement data retention policies
- Use encryption for stored conversations
- Comply with relevant regulations (GDPR, CCPA, etc.)

## Security Updates

Security updates are released as patch versions and announced via:

- GitHub Security Advisories
- Release notes
- Email to registered users (for critical issues)

## Acknowledgments

We thank the following researchers for responsibly disclosing vulnerabilities:

*No vulnerabilities reported yet.*

---

For any security questions, contact: **security@reasona.dev**
