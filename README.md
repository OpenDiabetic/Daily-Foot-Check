<!-- 🦶 Daily Foot Check -->

# 🦶 Daily Foot Check

**The 5-minute daily habit that could save your feet — as a free, local-first web app that runs anywhere.**

Part of [OpenDiabetic — The Digital Foot Lab](https://opendiabetic.com). Open it, do the daily check, and it keeps *your* history on *your* device so you can notice change day to day.

![local-first](https://img.shields.io/badge/local--first-yes-2FB67A) ![no data stored](https://img.shields.io/badge/data-never%20leaves%20your%20device-D99A2B) ![runs on the edge](https://img.shields.io/badge/runs%20on-a%20Raspberry%20Pi-3D9BE9) ![license](https://img.shields.io/badge/license-MIT-blue)

---

## The promises (our defendable values)

- **🔒 No data stored — anywhere but your device.** No account, no sign-in, no server database, no uploads. Your photos and history live in *your* browser, on *your* machine. We can't see them, because we never receive them.
- **🩺 It never diagnoses.** Educational monitoring only. It helps you *notice* change and decide when to involve your care team — early. It is **not a medical device**.
- **📟 Runs anywhere.** Pure static files — no backend, no GPU, no cloud, no dependencies. Serve it from a Raspberry Pi, a mini PC, an old laptop, or your phone.
- **🛠️ Run it yourself.** Don't trust us — host your own. That's a **Foot Check Node** (below).

---

## Quick start (30 seconds)

Clone it, serve the folder with any static web server, open it in a browser:

```bash
git clone https://github.com/SudoSuOps/Daily-Foot-Check.git
cd Daily-Foot-Check

# pick ONE:
python3 -m http.server 8080          # Python (built in everywhere)
npx serve .                          # Node
docker compose up                    # containerized (see below)
```

Then open **http://localhost:8080** — and, if you like, tap your browser's *"Add to Home Screen"* to run it like an app.

> **Camera note:** the browser camera only works in a *secure context* — that means `http://localhost` (fine) or `https://…`. Opening over a plain LAN IP (`http://192.168.x.x`) will block the camera. To use it from your phone against a **Foot Check Node**, serve it over HTTPS (see below).

---

## 📟 Run your own Foot Check Node

A **Foot Check Node** is any small box on your network — a Raspberry Pi, a ZimaBoard, a mini PC, an old laptop — that quietly serves Daily Foot Check to your household. Private, offline-capable, yours.

**With Docker (recommended for a persistent node):**
```bash
docker compose up -d          # serves on http://<node-ip>:8080
```

**With HTTPS (so phones on your LAN can use the camera):**
The included `docker-compose.yml` has a commented **Caddy** profile that issues an internal certificate:
```bash
docker compose --profile https up -d     # serves on https://<node-ip>
```
Trust the certificate once on each device, add it to your home screen, and you have a private household foot-check appliance — no cloud, no account, no data leaving the house.

**Bare metal (no Docker):**
```bash
# any static server works; e.g. with caddy:
caddy file-server --listen :8080 --root .
```

---

## How it works (the privacy architecture)

```
┌─────────────────────────────┐        the Foot Check Node
│  Your browser / your phone  │        just serves static files.
│  • camera capture           │        It NEVER receives your photos.
│  • compare today vs history │◀──────  index.html + app (HTML/JS/CSS)
│  • history in IndexedDB     │
│  • all on YOUR device       │
└─────────────────────────────┘
```

- **No backend.** The whole app is static files. The server's only job is to hand them to your browser.
- **Photos never upload.** Capture, comparison, and history all happen in the browser and are stored locally (IndexedDB). Clear your browser data and it's gone — because that's the only copy.
- **Optional AI review (roadmap):** if enabled, runs on a box *you* control (your own Node), processes a photo *in memory*, returns a calm observation, and **stores nothing**.

---

## What it is not

Daily Foot Check is **educational monitoring**. It does **not** diagnose, name a condition, tell you what is wrong, or replace your care team. If anything about your feet worries you — a wound that isn't healing, spreading redness or warmth, new pain or numbness — **contact your care team promptly.** In diabetic foot care, early is the entire strategy.

Prefer paper? The [Daily Foot Check Field Guide](https://opendiabetic.com/guides/daily-foot-check.html) is free to read or print.

---

## Roadmap

- **v0 — foundation** *(here now)*: project, license, self-host + Foot Check Node docs, branded shell.
- **v1 — the check**: guided daily capture, on-device history, calm day-to-day comparison — all client-side.
- **v2 — optional on-device review**: bring-your-own-Node AI observation (in memory, stores nothing).
- **Companion**: the native iOS app (FootLab) for the full experience.

## Contributing

PRs welcome — especially accessibility, translations, and edge-device packaging. Keep every change true to the promises above: **local-first, no data stored, never diagnoses.**

## License

**MIT** — run it, fork it, host it, share it. See [LICENSE](LICENSE). *(Not a medical device; see the notice in the license and above.)*

---

🐝 Part of the **Swarm & Bee** family · [opendiabetic.com](https://opendiabetic.com) · build@opendiabetic.com · Jupiter, FL
