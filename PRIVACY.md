# Privacy

## Data Handling

dockwatch-lite queries Docker containers and displays information available via the Docker API:
- Container names, IDs, and images
- Container state and port mappings
- CPU, memory, and I/O usage statistics
- Network interface statistics

This data is displayed locally and never transmitted externally by dockwatch-lite.

## Sample / Test Data

Tests use only synthetic sample data:
- Container IDs and names are short identifiers (`abcdef123456`, `nginx`, `db`)
- Network and disk I/O values are arbitrary test integers
- No real environment variables, credentials, or customer data appear in tests
