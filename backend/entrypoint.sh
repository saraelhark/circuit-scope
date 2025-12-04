#!/bin/bash
set -e

# Fix permissions for storage directory
# This ensures the volume mount is writable by the app user
mkdir -p /app/var/storage
chown -R app:app /app/var/storage

# Execute the command as app user
exec gosu app "$@"
