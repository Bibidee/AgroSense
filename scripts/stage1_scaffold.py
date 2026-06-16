"""
AgroSense - Stage 1 scaffolder.
Creates the Next.js App Router skeleton, design tokens, base config,
and .env.example. Idempotent: re-running overwrites generated files.
Run from project root:  python scripts/stage1_scaffold.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FILES: dict[str, str] = {}

# ---------- package.json ----------
FILES["package.json"] = r"""{
  "name": "agrosense",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "@supabase/ssr": "^0.5.2",
    "@supabase/supabase-js": "^2.45.4",
    "genlayer-js": "^0.10.0",
    "next": "15.0.3",
    "react": "19.0.0-rc-66855b96-20241106",
    "react-dom": "19.0.0-rc-66855b96-20241106",
    "viem": "^2.21.45",
    "zod": "^3.23.8"
  },
  "devDependencies": {
    "@types/node": "^22.9.0",
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "autoprefixer": "^10.4.20",
    "eslint": "^9.14.0",
    "eslint-config-next": "15.0.3",
    "postcss": "^8.4.49",
    "tailwindcss": "^3.4.14",
    "typescript": "^5.6.3"
  }
}
"""

# ---------- tsconfig ----------
FILES["tsconfig.json"] = r"""{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": false,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "baseUrl": ".",
    "paths": { "@/*": ["./*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules", "contract", "scripts"]
}
"""

FILES["next.config.mjs"] = r"""const nextConfig = {
  experimental: { serverActions: { bodySizeLimit: "8mb" } },
  images: { remotePatterns: [{ protocol: "https", hostname: "**" }] },
};
export default nextConfig;
"""

FILES["postcss.config.mjs"] = r"""export default { plugins: { tailwindcss: {}, autoprefixer: {} } };
"""

FILES["tailwind.config.ts"] = r"""import type { Config } from "tailwindcss";
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canopy:    "#0B3D2E",
        signal:    "#14B8A6",
        harvest:   "#D6A21E",
        clay:      "#B94A38",
        linen:     "#F6F1E8",
        ivory:     "#FFFCF5",
        charcoal:  "#17211D",
        olive:     "#68746D",
        sage:      "#D7DECF",
        consensus: "#6D5DF6",
      },
      fontFamily: {
        display: ["Sora", "ui-sans-serif", "system-ui"],
        body:    ["Inter", "ui-sans-serif", "system-ui"],
        mono:    ["IBM Plex Mono", "ui-monospace", "monospace"],
      },
      borderRadius: { xl: "14px", "2xl": "20px" },
    },
  },
  plugins: [],
};
export default config;
"""

FILES[".eslintrc.json"] = r"""{ "extends": "next/core-web-vitals" }
"""

FILES[".gitignore"] = r"""node_modules
.next
out
.env
.env.local
.env*.local
.vercel
.DS_Store
*.log
.supabase
__pycache__
*.pyc
"""

FILES[".env.example"] = r"""# ----- Supabase -----
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# ----- Wallet crypto (server only) -----
# 32-byte base64 secret used as an HKDF salt namespace for KDF stretching.
WALLET_KDF_PEPPER=

# ----- GenLayer StudioNet -----
GENLAYER_RPC_URL=https://studio.genlayer.com:8443/api
GENLAYER_CHAIN_ID=
NEXT_PUBLIC_GENLAYER_CONTRACT_ADDRESS=
# Server-side account private key used to submit advisory tx (StudioNet test account)
GENLAYER_SUBMITTER_PRIVATE_KEY=

# ----- App -----
NEXT_PUBLIC_APP_URL=http://localhost:3000
"""

# ---------- app/layout + globals ----------
FILES["app/globals.css"] = r"""@tailwind base;
@tailwind components;
@tailwind utilities;

@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
  color-scheme: light;
}
html, body { background: #F6F1E8; color: #17211D; font-family: Inter, ui-sans-serif, system-ui; }
.font-display { font-family: Sora, ui-sans-serif, system-ui; }
.font-mono { font-family: 'IBM Plex Mono', ui-monospace, monospace; }

.card { background: #FFFCF5; border: 1px solid #D7DECF; border-radius: 16px; }
.btn-primary { background: #0B3D2E; color: #FFFCF5; padding: 10px 18px; border-radius: 10px; font-weight: 600; }
.btn-primary:hover { background: #0e4d3a; }
.btn-ghost { background: transparent; color: #0B3D2E; padding: 10px 18px; border-radius: 10px; border: 1px solid #D7DECF; }
.badge-consensus { background: rgba(109,93,246,0.12); color: #6D5DF6; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; }
.badge-risk { background: rgba(185,74,56,0.12); color: #B94A38; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; }
.badge-ok { background: rgba(20,184,166,0.14); color: #14B8A6; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; }
"""

FILES["app/layout.tsx"] = r"""import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AgroSense — Consensus backed farm intelligence",
  description:
    "GenLayer powered farm decision platform: weather, soil, crop, and market uncertainty turned into consensus backed advisory verdicts.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
"""

# ---------- landing ----------
FILES["app/page.tsx"] = r"""import Link from "next/link";

export default function LandingPage() {
  return (
    <main className="min-h-screen">
      <nav className="max-w-6xl mx-auto flex items-center justify-between px-6 py-5">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-full bg-canopy grid place-items-center text-ivory font-display font-bold">A</div>
          <span className="font-display text-xl font-bold text-canopy">AgroSense</span>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/login" className="btn-ghost">Log in</Link>
          <Link href="/signup" className="btn-primary">Create account</Link>
        </div>
      </nav>

      <section className="max-w-6xl mx-auto px-6 pt-16 pb-24 grid md:grid-cols-2 gap-12 items-center">
        <div>
          <span className="badge-consensus">GenLayer powered</span>
          <h1 className="font-display text-5xl md:text-6xl font-bold text-canopy mt-5 leading-tight">
            Consensus backed<br/>farm intelligence.
          </h1>
          <p className="mt-5 text-lg text-olive max-w-lg">
            Turn weather, soil, crop, and market uncertainty into advisory verdicts judged by independent GenLayer validators — not a single black-box model.
          </p>
          <div className="mt-8 flex gap-3">
            <Link href="/signup" className="btn-primary">Create advisory case</Link>
            <Link href="/demo" className="btn-ghost">View demo verdict</Link>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-olive">ADVISORY · 0xA39E…7C21</span>
            <span className="badge-consensus">Validated by GenLayer</span>
          </div>
          <div className="mt-4">
            <div className="text-xs uppercase tracking-wider text-olive">Verdict</div>
            <div className="font-display text-3xl text-canopy font-bold mt-1">Delay planting</div>
          </div>
          <div className="grid grid-cols-2 gap-4 mt-6">
            <div>
              <div className="text-xs uppercase tracking-wider text-olive">Risk</div>
              <div className="mt-1"><span className="badge-risk">High rainfall</span></div>
            </div>
            <div>
              <div className="text-xs uppercase tracking-wider text-olive">Window</div>
              <div className="mt-1 font-display text-canopy">Re-review in 5 days</div>
            </div>
            <div>
              <div className="text-xs uppercase tracking-wider text-olive">Crop</div>
              <div className="mt-1 font-display text-canopy">Maize</div>
            </div>
            <div>
              <div className="text-xs uppercase tracking-wider text-olive">Region</div>
              <div className="mt-1 font-display text-canopy">Oyo, NG</div>
            </div>
          </div>
          <div className="mt-6 pt-4 border-t border-sage text-xs font-mono text-olive">
            tx 0x7f1c…be02 · source of truth: GenLayer Intelligent Contract
          </div>
        </div>
      </section>

      <footer className="border-t border-sage">
        <div className="max-w-6xl mx-auto px-6 py-6 text-sm text-olive flex justify-between">
          <span>© AgroSense</span>
          <span className="font-mono">GenLayer StudioNet</span>
        </div>
      </footer>
    </main>
  );
}
"""

# ---------- placeholder routes (filled in later stages) ----------
FILES["app/login/page.tsx"]            = "export default function P(){return <main className='p-10'>Login (Stage 3).</main>;}\n"
FILES["app/signup/page.tsx"]           = "export default function P(){return <main className='p-10'>Signup (Stage 3).</main>;}\n"
FILES["app/forgot-password/page.tsx"]  = "export default function P(){return <main className='p-10'>Forgot password (Stage 3).</main>;}\n"
FILES["app/reset-password/page.tsx"]   = "export default function P(){return <main className='p-10'>Reset password (Stage 3).</main>;}\n"
FILES["app/onboarding/page.tsx"]       = "export default function P(){return <main className='p-10'>Onboarding (Stage 3).</main>;}\n"
FILES["app/dashboard/page.tsx"]        = "export default function P(){return <main className='p-10'>Dashboard (Stage 4).</main>;}\n"
FILES["app/farms/page.tsx"]            = "export default function P(){return <main className='p-10'>Farms (Stage 4).</main>;}\n"
FILES["app/cases/new/page.tsx"]        = "export default function P(){return <main className='p-10'>New advisory case (Stage 4).</main>;}\n"
FILES["app/verdicts/[id]/page.tsx"]    = "export default function P(){return <main className='p-10'>Verdict (Stage 6).</main>;}\n"
FILES["app/evidence/page.tsx"]         = "export default function P(){return <main className='p-10'>Evidence room (Stage 4).</main>;}\n"
FILES["app/admin/page.tsx"]            = "export default function P(){return <main className='p-10'>Admin (Stage 6).</main>;}\n"
FILES["app/profile/page.tsx"]          = "export default function P(){return <main className='p-10'>Profile + Wallet (Stage 3).</main>;}\n"
FILES["app/settings/page.tsx"]         = "export default function P(){return <main className='p-10'>Settings (Stage 6).</main>;}\n"
FILES["app/demo/page.tsx"]             = "export default function P(){return <main className='p-10'>Demo verdict (static).</main>;}\n"

# ---------- README ----------
FILES["README.md"] = r"""# AgroSense

Consensus backed farm intelligence. GenLayer powered advisory verdicts.

## Stack
Next.js 15 (App Router) · Supabase (Auth + Postgres + Storage) · GenLayer StudioNet · Vercel

## Local dev
```bash
cp .env.example .env.local   # fill values
npm install
npm run dev
```

## Stages
1. **Scaffold** — this stage. Next.js skeleton + design tokens.
2. Supabase schema + RLS + Storage.
3. Auth + embedded wallet + recovery key.
4. Farms + advisory cases + evidence upload.
5. GenLayer `AgroSenseAdvisory` Intelligent Contract → deploy on StudioNet.
6. Verdict UI + admin + profile/wallet + settings.
7. Vercel deploy.

GenLayer is the source of truth for advisory verdicts. Supabase mirrors the on-chain result for product display only.
"""

# ---------- write everything ----------
def main() -> None:
    written = 0
    for rel, content in FILES.items():
        p = ROOT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        written += 1
    print(f"[stage1] wrote {written} files into {ROOT}")

if __name__ == "__main__":
    main()
