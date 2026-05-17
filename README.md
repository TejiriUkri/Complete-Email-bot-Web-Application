# 🤖 FollowUpBot — AI Email Follow-Up SaaS

An AI-powered email follow-up automation tool built with Streamlit, Groq AI, Gmail API, and Stripe.

---

## 📁 Project Structure

```
emailbot_app/
│
├── app.py                   # Main Streamlit entry point
├── webhook.py               # Stripe webhook listener (run separately)
├── requirements.txt
├── .env                     # Your credentials (never share)
│
├── pages/
│   ├── login.py             # Sign up / Login
│   ├── dashboard.py         # Bot controls + CSV upload + Gmail connect
│   ├── schedule.py          # Follow-up timing settings
│   ├── logs.py              # Activity log viewer
│   └── pricing.py           # Plans + Stripe checkout
│
├── auth/
│   └── user_db.py           # User accounts, trial tracking, plan limits
│
├── billing/
│   └── stripe_handler.py    # Stripe checkout + webhook verification
│
├── bot/                     # Copy all your bot files here
│   ├── main.py
│   ├── monitor_inbox.py
│   ├── write_email.py
│   ├── write_reply.py
│   ├── send_email.py
│   ├── read_csv.py
│   ├── gmail_auth.py
│   └── logger.py
│
├── data/
│   ├── users.json           # Auto-created when first user signs up
│   └── uploads/             # Per-user CSV and Gmail token storage
│
└── .streamlit/
    └── config.toml          # UI theme settings
```

---

## 🚀 Setup Guide

### Step 1 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 2 — Copy your bot files
Copy all files from your original email bot project into the `bot/` folder:
- `main.py`, `monitor_inbox.py`, `write_email.py`, `write_reply.py`
- `send_email.py`, `read_csv.py`, `gmail_auth.py`, `logger.py`

### Step 3 — Fill in your `.env` file
```
GROQ_API_KEY=your-groq-api-key
SENDER_EMAIL=you@gmail.com
SENDER_NAME=YourName
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_BASIC=price_...
STRIPE_PRICE_PRO=price_...
APP_URL=http://localhost:8501
```

### Step 4 — Set up Stripe
1. Go to [dashboard.stripe.com](https://dashboard.stripe.com)
2. Create two products: **Basic ($9/mo)** and **Pro ($29/mo)**
3. Copy the **Price IDs** (start with `price_`) into your `.env`
4. Go to **Webhooks** → Add endpoint:
   - URL: `http://your-server:4242/webhook`
   - Events: `checkout.session.completed`, `customer.subscription.deleted`
5. Copy the **Webhook Secret** into your `.env`

### Step 5 — Run the app
Open **two terminals**:

**Terminal 1 — Streamlit app:**
```bash
streamlit run app.py
```

**Terminal 2 — Stripe webhook listener:**
```bash
python webhook.py
```

---

## 💳 Pricing Plans

| Feature | Free Trial | Basic ($9/mo) | Pro ($29/mo) |
|---|---|---|---|
| Duration | 2 days | Monthly | Monthly |
| Max clients | 20 | 100 | Unlimited |
| Follow-up attempts | 1 | 3 | 5 |
| Daily send limit | 10 | 50 | 200 |
| Custom schedule | ❌ | ✅ | ✅ |
| Activity logs | ✅ | ✅ | ✅ |

---

## 🛑 Kill Switch

To stop a user's bot from the dashboard, click the **Stop Bot** button.
This creates a `STOP_{user}` file which the bot thread detects and shuts down cleanly.

---

## 🔒 Security Notes

- Passwords are hashed with SHA-256 before storage
- Gmail tokens are stored per-user in `data/uploads/`
- API keys are never stored in code — only in `.env`
- Stripe payments handled entirely by Stripe's secure hosted pages
- No credit card required for free trial

---

## 🌐 Deploying Online

To sell this publicly, deploy to **Railway**, **Render**, or **a VPS**:

1. Push your code to a private GitHub repo (add `.env` and `data/` to `.gitignore`)
2. Set environment variables in your hosting platform's dashboard
3. Update `APP_URL` in `.env` to your live domain
4. Point your Stripe webhook to your live domain

---

## 📞 Support

Check `bot_activity.log` for detailed bot activity.
All errors are caught and logged — check the **Activity Log** page in the app.
