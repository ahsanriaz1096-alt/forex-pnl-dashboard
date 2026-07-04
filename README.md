# Forex PnL Dashboard

Streamlit dashboard to track daily PnL, daily profit target %, tomorrow's projected
target, today/week/month PnL, a monthly calendar view, and a downloadable summary.

## Run locally (Windows)

```
pip install -r requirements.txt
streamlit run app.py
```

Opens at `http://localhost:8501`.

## Deploy on Streamlit Community Cloud (free, gives you a mobile link)

1. Push this folder to a new GitHub repo:
   ```
   git init
   git add .
   git commit -m "forex pnl dashboard"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<repo-name>.git
   git push -u origin main
   ```
2. Go to https://share.streamlit.io → **New app**.
3. Pick your repo, branch `main`, file `app.py` → **Deploy**.
4. You'll get a link like `https://<repo-name>.streamlit.app` — open it on your
   phone, add it to your home screen, and it behaves like an app.

## ⚠️ Important: data persistence on Streamlit Cloud

This app stores entries in `trades.csv` / `settings.csv` on disk. That works
perfectly when you run it locally, but **Streamlit Community Cloud's
filesystem is not permanent** — it resets on redeploys, app restarts, or after
long idle periods. Your logged trades can be wiped.

Two ways to handle this, pick one when you're ready:

- **Low-effort:** use the "Download Raw Trade Log (.csv)" button regularly as
  a backup, and re-upload if it ever resets (I can add an upload/restore box
  if you want).
- **Proper fix:** swap the CSV storage for a free persistent backend (Google
  Sheets via `gspread`, or a hosted SQLite/Postgres like Supabase/Turso).
  I can wire this up if you tell me which you'd prefer — takes ~15-20 min of
  changes.

For now the app works fully; just be aware of this before you rely on it for
weeks of history on the cloud deployment.

## Files

- `app.py` — the whole app
- `requirements.txt` — dependencies for Streamlit Cloud
- `trades.csv` — created automatically once you log your first entry
- `settings.csv` — created automatically when you save settings
