# Discord XP Bot

Bot dla naszego Discorda, który liczy XP tylko za voice i robi ranking – bez śmieciowych funkcji.

## MVP v0.1

### Core Features
* **XP za voice** - stała stawka 6 XP/min (1 XP za 10s w voice)
* **Zapis w Postgresie** - `total_xp`, `level`, `total_voice_sec`
* **Slash commands:**
  * `/rank [user]` - statystyki i pozycja w rankingu
  * `/leaderboard` - top 10 userów z medalami
* **Automatyczne role** - przydzielane na podstawie czasu w voice
  * Progi i role konfigurowalne w `config/roles_config.yaml`
  * Jedna ranga "voice" per user (bot zabiera poprzednie przy awansie)

### Ograniczenia (celowe!)
* ❌ Brak XP za wiadomości
* ❌ Brak decay/multiplikatorów
* ❌ Brak importów historycznych danych
* ✅ Config tylko dla jednego serwera (ID w pliku)

### Anti-abuse
* Ignore solo w kanale
* Ignore muted/deaf users
* Ignore kanał AFK
* Ignore kanały gdzie >50% to boty

## Tech Stack

**Bot:**
- py-cord v2 (discord.py fork)
- Python 3.11+
- asyncpg (async PostgreSQL)

**Infrastructure:**
- PostgreSQL 15
- Docker + docker-compose
- GitHub Actions CI

**Future (post-v0.1):**
- AWS EC2 deployment
- Terraform IaC

## Project Structure

```
discord-xp-bot/
  src/
    bot/
      __init__.py
      main.py          # Bot initialization
      commands.py      # Slash commands (/rank, /leaderboard)
      db.py            # Database layer (asyncpg)
      models.py        # Data models
      config.py        # Config loading (.env)
      roles.py         # Voice role management
  config/
    roles_config.yaml  # Role tiers configuration
  tests/
  scripts/
  docs/
    PROJECT_PLAN.md    # Detailed day-by-day plan
    level_calculator.py
  docker-compose.yml
  Dockerfile
  requirements.txt
  .env.example
```

## Quick Start (post-DAY02)

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your DISCORD_TOKEN

# Run locally
python -m src.bot.main
```

## Development Plan

Szybki plan 12-14 dni side-quest (1-2h/dzień):
- **DAY01-06**: Fundament (repo, bot, DB, commands, roles)
- **DAY07-09**: Voice tracking + XP logic + anti-abuse
- **DAY10-12**: Polish + Docker + CI
- **DAY13-14**: AWS deployment (opcjonalne)

Zobacz `docs/PROJECT_PLAN.md` dla szczegółów.

## License

MIT
