---
name: Frappe HR setup
description: How the Frappe HR project is configured to run in Replit without a full Frappe bench stack.
---

## Context
Frappe HR is a Frappe Framework app requiring MariaDB, Redis, and a full bench environment. In Replit, only the Vue/Vite frontend (`frontend/`) can run standalone.

## Key setup decisions

- Frontend dev server runs on port 5000 with `host: "0.0.0.0"`.
- `frappe-ui/vite.js` plugin overrides the port — must pass `frappeui({ port: 5000 })` explicitly.
- Import path `frappe-ui/vite` → must use `frappe-ui/vite.js` (no extension causes module resolution failure).
- Created `/home/runner/workspace/sites/common_site_config.json` and `/home/runner/workspace/apps/` so the bench detection logic in vite.js finds a valid bench root.
- Added vite alias `"../../../../sites/common_site_config.json"` → `../sites/common_site_config.json` for `src/socket.js`.
- Stubbed `frontend/public/frappe-push-notification.js` (removed Firebase imports — Firebase was removed from package.json to avoid download hangs).
- Removed Firebase (`firebase`, `vite-plugin-pwa`, `workbox-*`) from `frontend/package.json` to keep install fast.
- yarn.lock removed (was resolving from `mirror2.chabokan.net` which is blocked in Replit); npm install works with Replit's local registry.

**Why:** `/home` filesystem is read-only in Replit, so files must live under `/home/runner/workspace/`.
