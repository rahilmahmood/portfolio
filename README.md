# Engineering Portfolio

Next.js 14 + Sanity CMS. Edit content at `/studio`, deploy to Vercel for free.

---

## Setup (one-time, ~15 min)

### 1. Install dependencies

```bash
npm install
```

### 2. Create a free Sanity project

1. Go to [sanity.io](https://sanity.io) and sign up (free)
2. Create a new project — name it anything, choose **Production** dataset
3. Copy your **Project ID** from the project dashboard

### 3. Configure environment variables

```bash
cp .env.local.example .env.local
```

Open `.env.local` and fill in your Project ID:

```
NEXT_PUBLIC_SANITY_PROJECT_ID=abc123xyz
NEXT_PUBLIC_SANITY_DATASET=production
```

### 4. Run locally

```bash
npm run dev
```

- Portfolio: [http://localhost:3000](http://localhost:3000)
- CMS Studio: [http://localhost:3000/studio](http://localhost:3000/studio)

### 5. Add your first project in the CMS

Go to `localhost:3000/studio` → click **Project** → **New** and fill in the fields.

---

## Deploying to Vercel

1. Push this folder to a new GitHub repo
2. Go to [vercel.com](https://vercel.com) → **New Project** → import the repo
3. Under **Environment Variables**, add:
   - `NEXT_PUBLIC_SANITY_PROJECT_ID` = your project ID
   - `NEXT_PUBLIC_SANITY_DATASET` = `production`
4. Click **Deploy** — done.

### Connecting your custom domain

In Vercel: **Project Settings → Domains → Add Domain** → type your domain.
Then at your domain registrar (Namecheap, Cloudflare, etc.) add the DNS records Vercel shows you. Takes 5 min.

---

## Customizing your info

All personal details are at the top of these files — look for `// ── Edit` comments:

| What | File |
|---|---|
| Your name | `components/Nav.tsx`, `app/layout.tsx` |
| Resume & LinkedIn | `app/page.tsx`, `app/about/page.tsx` |
| Bio & skills | `app/about/page.tsx` |
| "Currently" section | `app/page.tsx` → `CURRENTLY` array |
| Accent color | `app/globals.css` → `--accent` |

---

## Managing content (after setup)

Go to `yourdomain.com/studio` to:

- **Add a project** — fill title, date, category, summary, hero image, tools, and the case study sections
- **Set featured** — toggle "Featured on Home" to show a project on the home page
- **Update a project** — click it, edit, save — site rebuilds within 60 seconds
- **Add gallery images** — drag images into the Gallery field on any project; they appear as a horizontal scroll on the project page

---

## Stack

- **Framework**: Next.js 14 App Router (static + ISR)
- **CMS**: Sanity v3 (free tier)
- **Hosting**: Vercel (free tier)
- **Fonts**: Space Grotesk, JetBrains Mono (via next/font)
- **Images**: Sanity CDN + next/image
