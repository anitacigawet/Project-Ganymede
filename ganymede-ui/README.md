# Project Ganymede UI

One Next.js interface supports two build-time editions:

```bash
npm run dev             # full local edition; connects to FastAPI on port 8000
npm run build           # production full build
npm run dev:showcase    # deterministic fictional run; no backend calls
npm run build:showcase  # static export to out/
npm run serve:showcase  # serve an existing static export on loopback
```

The root [README](../README.md) contains complete setup instructions.
