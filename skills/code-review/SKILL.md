---
name: code-review
description: Automated code review with security, performance, and style analysis
metadata: {"openclaw": {"requires": {"bins": ["python"]}, "emoji": "🔍"}}
---

# Code Review Skill

When asked to review code, follow this structured approach:

## 1. Security Analysis
- Check for injection vulnerabilities (SQL, XSS, command injection)
- Verify input validation and sanitization
- Review authentication and authorization logic
- Check for sensitive data exposure

## 2. Performance Review
- Identify N+1 query patterns
- Check for unnecessary memory allocations
- Review algorithmic complexity
- Look for blocking operations in async code

## 3. Code Quality
- Verify error handling completeness
- Check for resource leaks (file handles, connections)
- Review naming conventions and readability
- Identify code duplication

## 4. Testing
- Assess test coverage of the changed code
- Check edge case handling in tests
- Verify mock usage is appropriate

Use the `skill_code-review` tool with `{"input": "<code or file path>"}` to invoke this skill.
