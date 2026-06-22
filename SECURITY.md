# Security Policy

## Reporting Issues

If you discover a security vulnerability, please email alibidhendi2000@gmail.com with details. Do not open a public issue.

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact

## What Not to Commit

Never commit to this repository:
- Docker socket paths from production environments
- API credentials or authentication tokens
- Container environment variables containing secrets
- Private registry credentials
- Personal or sensitive container data
- Real customer/business data from running containers

Use environment variables and `.gitignore` for sensitive configuration.

## Known Limitations

- dockwatch-lite requires access to the Docker Unix socket (typically `/var/run/docker.sock`)
- The user running dockwatch must have appropriate permissions for the socket
- Stats are collected via Docker Remote API; availability depends on daemon support
- No encryption for daemon communication—ensure socket is on a trusted local system
