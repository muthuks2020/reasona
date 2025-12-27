# Contributing to Reasona

Thank you for your interest in contributing to Reasona! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## How to Contribute

### Reporting Bugs

1. **Search existing issues** to avoid duplicates
2. **Create a new issue** with:
   - Clear, descriptive title
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (Python version, OS, Reasona version)
   - Minimal reproducible example if possible

### Suggesting Features

1. **Check existing issues and discussions** for similar ideas
2. **Open a feature request** with:
   - Clear description of the feature
   - Use case and motivation
   - Proposed implementation (optional)
   - Any alternatives considered

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Set up development environment**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/reasona.git
   cd reasona
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```
3. **Make your changes** following our coding standards
4. **Add tests** for new functionality
5. **Run the test suite**:
   ```bash
   pytest
   ```
6. **Run linting and formatting**:
   ```bash
   ruff check src tests
   ruff format src tests
   mypy src
   ```
7. **Commit your changes** with clear, descriptive messages
8. **Push and create a Pull Request**

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/reasona.git
cd reasona

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (optional but recommended)
pip install pre-commit
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=reasona --cov-report=html

# Run specific test file
pytest tests/test_core.py

# Run specific test
pytest tests/test_core.py::test_conductor_creation -v
```

### Code Style

We use the following tools to maintain code quality:

- **Ruff** for linting and formatting
- **mypy** for type checking
- **Black** style formatting (via Ruff)

Configuration is in `pyproject.toml`. Run checks with:

```bash
# Lint
ruff check src tests

# Format
ruff format src tests

# Type check
mypy src
```

## Project Structure

```
reasona/
├── src/reasona/
│   ├── core/           # Core components (Conductor, Synapse, Workflow)
│   ├── tools/          # Tool system and built-in tools
│   ├── integrations/   # LLM provider integrations
│   ├── server/         # REST API server
│   ├── mcp/            # HyperMCP server
│   └── cli/            # Command-line interface
├── tests/              # Test suite
├── docs/               # Documentation
└── examples/           # Example scripts
```

## Coding Standards

### Python Style

- Follow PEP 8 guidelines
- Use type hints for all function signatures
- Write docstrings for public classes and methods
- Keep functions focused and under 50 lines when possible

### Naming Conventions

- Classes: `PascalCase`
- Functions/methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private members: `_leading_underscore`

### Documentation

- Update docstrings when changing functionality
- Update README for user-facing changes
- Add examples for new features

### Testing

- Write tests for all new functionality
- Maintain or improve test coverage
- Use descriptive test names
- Include both positive and negative test cases

## Areas for Contribution

### Good First Issues

Look for issues labeled `good first issue` - these are ideal for newcomers.

### Priority Areas

- **New LLM Providers**: Add support for additional providers
- **Built-in Tools**: Create useful new tools
- **Documentation**: Improve guides and examples
- **Testing**: Increase test coverage
- **Performance**: Optimize critical paths

### Architecture Contributions

For significant changes, please open an issue first to discuss the approach.

## Review Process

1. All PRs require at least one review
2. CI checks must pass
3. New code must have tests
4. Documentation must be updated

## Release Process

Releases are managed by maintainers following semantic versioning:

- **Patch** (0.0.x): Bug fixes
- **Minor** (0.x.0): New features, backward compatible
- **Major** (x.0.0): Breaking changes

## Getting Help

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and general discussion
- **Documentation**: https://reasona.dev/docs

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Reasona! 🚀
