# Git Workflow - Discord XP Bot

## Branch Strategy

**Main branches:**
- `main` - stabilne wersje, gotowe do deploy
- `develop` - aktywny development, codzienne commity

## Merge Strategy: Milestone-based (Opcja 2)

Merge `develop` → `main` na **3 kluczowe momenty**:

### 1️⃣ DAY06.5 - Fundament + Commands
**Co jest gotowe:**
- ✅ Repo setup (DAY01)
- ✅ Bot z /ping (DAY02)
- ✅ Postgres + docker-compose (DAY03)
- ✅ DB layer + roles config (DAY04)
- ✅ /leaderboard (DAY05)
- ✅ /rank (DAY06)
- ✅ Role manager helper (DAY06.5)

**Status:** Można testować commands ręcznie (bez voice tracking)
**Merge jako:** `chore: merge DAY01-06.5 - fundament + commands`

---

### 2️⃣ DAY09 - v0.1 RELEASE 🎯
**Co jest gotowe:**
- ✅ Voice tracking (DAY07)
- ✅ Real XP + leveling + role assignment (DAY08)
- ✅ Anti-abuse logic (solo/muted/AFK/bots) (DAY09)

**Status:** **Bot w pełni funkcjonalny** - główny milestone!
**Merge jako:** `release: v0.1 - Discord XP bot fully functional`
**Tag:** `v0.1`

---

### 3️⃣ DAY12 - Production-ready
**Co jest gotowe:**
- ✅ Level-up logging + config (DAY10)
- ✅ Admin commands (/addxp, /resetstats, /syncvoice) (DAY10.5)
- ✅ Dockerfile + full docker-compose (DAY11)
- ✅ CI pipeline (GitHub Actions) (DAY12)

**Status:** Deployment-ready (Docker + CI)
**Merge jako:** `release: v0.1.1 - production-ready (Docker + CI)`
**Tag:** `v0.1.1`

---

### Opcjonalnie: DAY14 - AWS Deployment
Jeśli robisz AWS (FAZA 4):
- Merge po DAY14 jako `release: v0.1.2 - AWS deployment`
- Tag: `v0.1.2`

---

## Commit Convention

Format: `[XPBOT][DAY##] Description`

**Przykłady:**
```bash
[XPBOT][DAY01] Init repo + README + project structure
[XPBOT][DAY02] Minimal bot with /ping (py-cord)
[XPBOT][DAY03] Postgres via docker-compose + schema
[XPBOT][DAY04] DB layer + roles config loader
[XPBOT][DAY05] /leaderboard command (top 10 with medals)
[XPBOT][DAY06] /rank command + position calculation
[XPBOT][DAY06.5] Voice role manager (with hierarchy checks)
[XPBOT][DAY07] Voice state tracking + active_sessions recovery
[XPBOT][DAY08] Real XP ticking + leveling + role assignment
[XPBOT][DAY09] Anti-abuse: solo/muted/AFK ignore + tests
[XPBOT][DAY10] Level-up logging + config placeholder
[XPBOT][DAY10.5] Admin commands: /addxp, /resetstats, /syncvoice
[XPBOT][DAY11] Dockerfile + full docker-compose
[XPBOT][DAY12] CI with pytest + docker build
```

---

## Quick Reference

**Codzienne workflow:**
```bash
# Na develop
git checkout develop
git add -A
git commit -m "[XPBOT][DAY##] ..."
git push origin develop
```

**Merge milestones:**
```bash
# Po DAY06.5, DAY09, DAY12
git checkout main
git merge develop --no-ff -m "chore: merge DAY##..."
git tag v0.1  # tylko dla DAY09 i DAY12
git push origin main --tags
```

---

## Status Tracking

- [ ] DAY01-06.5 → Fundament
- [ ] DAY07-09 → v0.1 Core
- [ ] DAY10-12 → v0.1.1 Production
- [ ] DAY13-14 → v0.1.2 AWS (optional)
