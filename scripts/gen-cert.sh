#!/usr/bin/env bash
# Generate a self-signed TLS certificate for pi-control-mcp.
# Run this on the Raspberry Pi once, then reference the paths in pi-control.toml.
#
# Usage: ./scripts/gen-cert.sh [output-dir]
#   output-dir defaults to ~/.config/pi-control-mcp/certs

set -euo pipefail

OUT_DIR="${1:-$HOME/.config/pi-control-mcp/certs}"
mkdir -p "$OUT_DIR"

CERT="$OUT_DIR/server.crt"
KEY="$OUT_DIR/server.key"

# Use the Pi's hostname or IP as the CN / SAN
HOSTNAME="$(hostname -f 2>/dev/null || hostname)"

openssl req -x509 -newkey rsa:4096 -sha256 -days 3650 -nodes \
  -keyout "$KEY" \
  -out "$CERT" \
  -subj "/CN=$HOSTNAME" \
  -addext "subjectAltName=DNS:$HOSTNAME,DNS:raspberrypi.local,IP:127.0.0.1"

chmod 600 "$KEY"

echo ""
echo "Certificate : $CERT"
echo "Private key : $KEY"
echo ""
echo "Add to pi-control.toml:"
echo "  ssl_certfile = \"$CERT\""
echo "  ssl_keyfile  = \"$KEY\""
echo ""
echo "To trust this cert on your client machine, copy server.crt and add it to"
echo "your OS trust store, or pass it as a custom CA when connecting."
