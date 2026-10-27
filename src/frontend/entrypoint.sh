#!/bin/sh

set -eu

cat > /usr/share/nginx/html/runtime-config.js <<'EOF'
window.RUNTIME_CONFIG = {
  API_URL: window.location.origin
};
console.log("Runtime config loaded:", window.RUNTIME_CONFIG);
EOF

exec /docker-entrypoint.sh nginx -g "daemon off;"