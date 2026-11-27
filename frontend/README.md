# ECOINTEL Frontend (dark redesign)
```
cd frontend && npm install && npm run dev      # http://localhost:5173
npm run build                                  # type-check + production build
```
Start FastAPI on http://127.0.0.1:8000 first. Vite proxies /investigations to it (HashRouter keeps UI routes from clashing).
Replace your existing `frontend/` folder with this one (backend untouched). Missing API data is shown as "Not available", never fabricated.
