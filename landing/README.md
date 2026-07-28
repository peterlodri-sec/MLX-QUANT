# AXIOM QUANT — Cloudflare Free Tier Landing Page

Pristine, museum-grade **'S00N'** landing page for **`axiomquant.org`**, built with pure HTML5, CSS3, and an interactive 2D Spectral Canvas animation engine.

---

## ⚡ Deployment Instructions (100% Free on Cloudflare Pages)

### Step 1: Purchase `axiomquant.org` via Cloudflare Registrar
1. Log into your [Cloudflare Dashboard](https://dash.cloudflare.com/).
2. Go to **Domain Registration** → **Register Domains**.
3. Search for **`axiomquant.org`** and complete registration (Cloudflare sells domains at wholesale cost with 0% markup).

### Step 2: Deploy to Cloudflare Pages

#### Option A: Direct CLI Deployment (Fastest)
From this project directory, run:
```bash
# 1. Login to Cloudflare Wrangler (if not already logged in)
npx wrangler login

# 2. Deploy the landing folder to Cloudflare Pages
npx wrangler pages deploy landing --project-name=axiomquant-landing
```

#### Option B: GitHub Integration (Continuous Deployment)
1. Push this repository or `landing` directory to GitHub.
2. In Cloudflare Dashboard, go to **Workers & Pages** → **Create Application** → **Pages** → **Connect to Git**.
3. Select your repository, set the **Build output directory** to `landing`, and click **Save and Deploy**.

### Step 3: Attach Custom Domain (`axiomquant.org`)
1. In Cloudflare Dashboard, open your project **axiomquant-landing** under **Workers & Pages**.
2. Click **Custom domains** → **Add Custom Domain**.
3. Enter `axiomquant.org` (and `www.axiomquant.org`).
4. Cloudflare will automatically route your free SSL/TLS certificate and edge CDN cache!

---

## 🎨 Visual Features
- **Spectral Canvas Engine**: Real-time rendering of concentric precision circles, Golden Ratio ($\phi = 1.618$) spiral, quantum superposition waveforms, and mouse-reactive stochastic particles.
- **Museum Telemetry UI**: Clinical monospaced header, live latency ticker, matrix array accents, and responsive access request waitlist.
- **Zero Dependencies**: Pure native JavaScript, HTML5, and CSS3—loads in under <50ms worldwide.
