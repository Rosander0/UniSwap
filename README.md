# UniSwap 🎓

> Campus-only peer-to-peer marketplace where university students buy, sell, and exchange used textbooks, graphing calculators, lab coats, and electronics.

---

## 🌐 GitHub Pages Showcase

The static documentation and technical showcase site is hosted on GitHub Pages:
**`https://<username>.github.io/<repo-name>/`**

### GitHub Pages Setup Instructions
To serve the static showcase from your repository:
1. Navigate to your repository settings on GitHub: **Settings &rarr; Pages**.
2. Under **Build and deployment &rarr; Source**, select **Deploy from a branch**.
3. Under **Branch**, select `main` and set the folder to `/docs`.
4. Click **Save**.
5. GitHub Pages will serve `docs/index.html` as the landing page. (The `docs/.nojekyll` file ensures underscore-prefixed assets are not ignored by Jekyll).

> **Note on Static Showcase & Screenshots:**
> The `docs/` folder contains pure static HTML and CSS with embedded SVG architecture and state machine diagrams. To supplement the showcase with live screenshots of the running Django UI, capture the following views and place them into `docs/assets/`:
> - `screenshot_listings.png` (Browse items grid with filter bar)
> - `screenshot_detail.png` (Listing detail page with photo gallery)
> - `screenshot_chat.png` (Peer-to-peer conversation interface)
> - `screenshot_deals.png` (Transaction lifecycle dashboard)
> - `screenshot_profile.png` (Seller profile with dynamic average star rating)

---

## 🚀 Features & Architecture

- **Campus Institutional Verification Gate:** Users must register with an email domain matching an active `Campus` entry (e.g. `@state.edu`). Verification links are signed using Django's cryptographic `TimestampSigner`.
- **Zero-IDOR Access Control:** Every view handling conversations, transactions, or reviews filters by active participant (`buyer` or `seller`) before running `get_object_or_404`, returning 404 to any non-participant.
- **Enforced State Machine:** Transaction workflow: `Requested &rarr; Agreed (seller only) &rarr; Completed (buyer or seller)`. Completing a transaction automatically updates listing status to `Sold`.
- **Soft Delete for Listings:** Deleting a listing marks its status as `Removed` instead of dropping the row, preserving audit trails.
- **Tamper-Proof Reputation:** Only parties of a completed transaction can review each other. Seller ratings are computed live with Django's `Avg` aggregate.

---

## 🛠️ Tech Stack

- **Backend:** Python 3.12+, Django 5.x
- **Database:** SQLite (default for development), PostgreSQL via `DATABASE_URL` (production)
- **Image Uploads:** Pillow (`ImageField`)
- **Frontend:** Server-rendered Django templates, Vanilla CSS (zero build tools required)
- **Testing:** Django's native test runner (`manage.py test`)

---

## 💻 Local Setup & Development

### 1. Prerequisites
- Python 3.12+ (or compatible Python 3 runtime)
- Git

### 2. Clone Repository & Setup Virtual Environment
```bash
git clone https://github.com/<username>/<repo-name>.git
cd uniswap

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Windows (CMD):
.venv\Scripts\activate.bat
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Default `.env` configuration:
```env
DJANGO_SECRET_KEY=local-dev-secret-key-replace-in-production
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,testserver
DATABASE_URL=sqlite:///db.sqlite3
```

### 5. Run Migrations
```bash
python manage.py migrate
```

### 6. Seed Sample Data
Populate categories (Textbooks, Calculators, Lab Coats, Electronics, Other), a sample campus (`State University`, `@state.edu`), demo users, and listings:
```bash
python manage.py seed_data
```

### 7. Run Development Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.

#### Demo Credentials Created by `seed_data`:
- **Verified Seller:** `alice_senior` / `StudentPass123!` (`alice@state.edu`)
- **Verified Buyer:** `bob_sophomore` / `StudentPass123!` (`bob@state.edu`)

*(Verification emails in development are printed directly to the console via Django's console email backend).*

---

## 🧪 Running the Test Suite

Run all 32 unit and cross-app integration tests:
```bash
python manage.py test
```

### What the Tests Verify:
1. **Verification Gate:** Unverified users are blocked and redirected to `/accounts/verify-notice/`.
2. **Ownership:** Non-owners cannot edit or delete listings (HTTP 403), and deletion sets status to `Removed`.
3. **IDOR Immunity:** Non-participants receive HTTP 404 on conversation, deal, and review routes.
4. **Transaction State Machine:** Invalid state jumps and unauthorized role transitions raise HTTP 400.
5. **Review Gate & Rating Aggregation:** Reviews rejected before completion, duplicate reviews blocked, and `Avg` rating calculates accurately.
6. **Campus Domain Signup:** Registration rejects any non-institutional email domain.

---

## 🚢 Deployment Guide (Python Host / Production)

To deploy UniSwap on a Python host (such as Render, Railway, Fly.io, or Heroku):

1. **Environment Variables:** Set the following variables in your hosting provider's dashboard:
   - `DJANGO_SECRET_KEY`: Long, cryptographically secure random string.
   - `DJANGO_DEBUG`: `False`
   - `DJANGO_ALLOWED_HOSTS`: Your production domain (e.g., `uniswap.onrender.com`).
   - `DATABASE_URL`: Managed PostgreSQL connection string (`postgres://...`).
   - `DJANGO_EMAIL_BACKEND`: SMTP backend configuration (SendGrid, Mailgun, AWS SES, or SMTP).

2. **Collect Static Files:**
   ```bash
   python manage.py collectstatic --noinput
   ```

3. **Run Migrations on Deploy:**
   ```bash
   python manage.py migrate
   ```

4. **WSGI Server:** Launch with `gunicorn` or `uvicorn`:
   ```bash
   gunicorn uniswap.wsgi:application --bind 0.0.0.0:$PORT
   ```

5. **Media Storage:** In production, configure object storage (e.g. AWS S3 or Cloudinary) for persistent student upload images.

---

## 📄 License
MIT License. Built for university campus marketplaces.

