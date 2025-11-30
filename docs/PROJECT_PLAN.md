Założenia tego planu:

* To jest **side quest** – max 1–2h na „dzień” projektu
* Cel v0.1: **bot z XP za voice + /rank + /leaderboard + zapis w Postgresie**.
* Level-up message dopiero PO v0.1.
* AWS/Terraform / K8s = drugi etap, jak core działa.

Możesz nazwać commity np. `[XPBOT][DAY01] Init repo` itd.

---

## FAZA 1 – FUNDAMENT APLIKACJI (bez voice, bez XP, sam ranking)

### DAY01 – Definicja projektu + repo

**Cel:** mieć jasny scope i repo gotowe do pracy.

* Dodaj `README.md` z:

  * krótkim opisem:

    > Bot dla naszego Discorda, który liczy XP tylko za voice i robi ranking – bez śmieciowych funkcji.
  * **MVP v0.1** – wypunktuj:

    * XP za voice (stała stawka, np. 6 XP/min)
    * zapis `total_xp`, `level`, `total_voice_sec` w DB
    * `/rank`, `/leaderboard`
    * **role przydzielane na podstawie czasu w voice** (progi i role w `roles_config.yaml`)
    * brak message XP, brak decay, brak multiplikatorów, brak importów
  * **Ograniczenia:**

    * jedna ranga „voice" per user (bot zabiera poprzednie rangi przy awansie)
    * config tylko dla mojego serwera (ID wpisane w pliku)
* Dodaj podstawową strukturę katalogów:

  ```text
  discord-xp-bot/
    src/
      bot/
        __init__.py
        main.py
        commands.py
        db.py
        models.py
        config.py
        roles.py
    config/
      roles_config.yaml
    tests/
    .gitignore
    pyproject.toml / requirements.txt
  ```

**Gotowe, gdy:** masz repo, README z jasno opisanym MVP i pusty szkielet katalogów.

---

### DAY02 – Minimalny bot + /ping

**Cel:** bot się łączy z Discordem i reaguje.

* Skonfiguruj venv, dodaj dependencje:

  ```bash
  pip install py-cord python-dotenv asyncpg
  ```

  *(używamy `py-cord` v2 - oficjalny discord.py jest martwy od 2022)*
* W `config.py`:

  * wczytywanie tokena z `.env` (użyj `python-dotenv` albo własny wrapper).
* W `main.py`:

  * stwórz bota ze slash commands (`app_commands`).
  * dodaj `/ping`, który zwraca np. „XPBot online”.
* Odpal lokalnie, sprawdź że `/ping` działa na twoim serwerze testowym.

**Gotowe, gdy:** bot stoi lokalnie i `/ping` odpowiada.

---

### DAY03 – Postgres + docker-compose

**Cel:** mieć lokalną bazę gotową na ranking.

* Stwórz `docker-compose.yml` z:

  * usługą `db` (Postgres),
  * volume na dane,
  * hasło/user/db z `.env`.

* Dodaj plik `schema.sql` lub prosty migrator (na start może być czyste SQL).

* Zdefiniuj tabelę `user_stats`:

  ```sql
  CREATE TABLE user_stats (
      guild_id        BIGINT NOT NULL,
      user_id         BIGINT NOT NULL,
      total_xp        INTEGER NOT NULL DEFAULT 0,
      level           INTEGER NOT NULL DEFAULT 0,
      xp_into_level   INTEGER NOT NULL DEFAULT 0,
      total_voice_sec BIGINT NOT NULL DEFAULT 0,
      last_voice_join TIMESTAMPTZ NULL,  -- tracking ostatniego join (do recovery po restarcie)
      updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      PRIMARY KEY (guild_id, user_id)
  );
  ```

* Odpal `docker-compose up -d`, załaduj schema.

**Gotowe, gdy:** masz Postgresa w dockerze z tabelą `user_stats`.

---

### DAY04 – Warstwa DB + testowe zapisy

**Cel:** umiesz czytać/zapisywać ranking.

* W `db.py`:

  * funkcja do tworzenia połączenia (użyj `asyncpg` - jest async i szybszy niż psycopg).
  * helpery:

    * `get_user_stats(guild_id, user_id)`
    * `upsert_user_stats(...)`
* Zrób prosty skrypt (np. `scripts/seed.py`), który:

  * wrzuci kilku userów z przykładowym XP, level i total_voice_sec.
* Sprawdź SELECT-em z poziomu Pythona.

**Gotowe, gdy:** możesz z Pythona wstawić i pobrać wpis z `user_stats`.

**DODATKOWO:** Utwórz plik konfiguracyjny ról:

* Stwórz `config/roles_config.yaml`:

  ```yaml
  guilds:
    "123456789012345678":  # ID twojego serwera
      tiers:
        - name: Rookie
          role_id: 111111111111111111
          min_minutes: 0
        - name: Regular
          role_id: 222222222222222222
          min_minutes: 300   # 5h
        - name: Grinder
          role_id: 333333333333333333
          min_minutes: 1200  # 20h
        - name: No-Life
          role_id: 444444444444444444
          min_minutes: 3600  # 60h
  ```

* W `src/bot/roles.py` napisz prosty loader:

  ```python
  # src/bot/roles.py
  from dataclasses import dataclass
  from typing import List, Optional

  @dataclass
  class RoleTier:
      role_id: int
      min_minutes: int

  @dataclass
  class GuildRolesConfig:
      guild_id: int
      tiers: List[RoleTier]

  def load_roles_config(path: str = "config/roles_config.yaml") -> dict[int, GuildRolesConfig]:
      ...
  ```

* Funkcja ładuje plik i trzyma w pamięci: `roles_config[guild_id] -> GuildRolesConfig`.

---

### DAY05 – /leaderboard (na fejkowych danych)

**Cel:** mieć działający ranking zanim dotkniesz voice.

* W `commands.py` dodaj komendę `/leaderboard`:

  * bierze `interaction.guild.id`,
  * odpala SELECT:

    ```sql
    SELECT user_id, total_xp, level, total_voice_sec
    FROM user_stats
    WHERE guild_id = $1
    ORDER BY total_xp DESC, total_voice_sec DESC, user_id ASC
    LIMIT 10;
    ```
  * buduje embed:

    * top 3 z 🥇🥈🥉
    * reszta zwykłe numerki.
* Na razie bazuje na „seedowanych” danych z DAY04.

**Gotowe, gdy:** `/leaderboard` na realnym serwerze pokazuje sensowną tabelę z fejkowymi danymi.

---

### DAY06 – /rank (pojedynczy użytkownik)

**Cel:** podgląd swojej pozycji + statystyki.

* Dodaj komendę `/rank [user]`:

  * jeśli brak parametru → bierze autora.
  * pobiera stats z DB.
  * dodatkowo liczy pozycję w rankingu:

    * albo jednym sprytnym SQL z window function (ROW_NUMBER),
    * albo na start: prosty SELECT sorted + enumerate w Pythonie (do 1000 userów wystarczy).
  * embed:

    * `nick`,
    * `level`,
    * `XP: xp_into_level / xp_needed`,
    * `Total XP`,
    * `Time in voice: Xh Ym`,
    * `Position: #N`.

**Gotowe, gdy:** `/rank` działa na testowych danych i pokazuje pozycję w rankingu.

---

### DAY06.5 – Helper do przydzielania ról

**Cel:** mieć czystą funkcję, która na podstawie `total_voice_sec` i `roles_config` zarządza rolami usera.

* W `roles.py` dodaj:

  ```python
  async def update_user_voice_role(
      member: discord.Member,
      guild_roles: GuildRolesConfig,
      total_voice_sec: int,
  ) -> None:
      # Sprawdź permisje bota
      if not member.guild.me.guild_permissions.manage_roles:
          logger.error(f"Bot missing MANAGE_ROLES in {member.guild.id}")
          return

      minutes = total_voice_sec // 60

      # znajdź najwyższą role tier, którą user powinien mieć
      eligible_tier = max(
          (tier for tier in guild_roles.tiers if minutes >= tier.min_minutes),
          key=lambda t: t.min_minutes,
          default=None,
      )

      # jeśli żadna ranga nie pasuje -> zabierz wszystkie voice-role i wyjdź
      voice_role_ids = {tier.role_id for tier in guild_roles.tiers}

      # Sprawdź role hierarchy - bot role musi być wyżej niż tier roles
      bot_top_role = member.guild.me.top_role
      # ... logika modyfikacji member.roles (+ check hierarchy)
  ```

* Na tym etapie możesz:

  * tylko logować, co *byś nadał/zabrał*,
  * albo podpiąć się do testowego serwera z fake'owymi rolami.

**Gotowe, gdy:** masz czystą funkcję, która decyduje *jakie role powinna mieć osoba* na podstawie czasu.

---

## FAZA 2 – VOICE LOGIC + XP (prawdziwy silnik)

### DAY07 – Voice tracking w pamięci (bez XP)

**Cel:** dobrze łapać join/leave, zanim dotkniesz XP.

* Zaimplementuj event `on_ready()`:

  ```python
  @bot.event
  async def on_ready():
      # Odbuduj active_sessions ze wszystkich voice channels
      # (ważne po restarcie bota, żeby nie tracić trackingu)
      for guild in bot.guilds:
          for channel in guild.voice_channels:
              for member in channel.members:
                  if not member.bot:  # ignoruj boty
                      # Spróbuj odzyskać last_voice_join z DB (opcjonalne)
                      stats = await get_user_stats(guild.id, member.id)
                      joined_at = stats.last_voice_join if stats and stats.last_voice_join else datetime.utcnow()

                      active_sessions[(guild.id, member.id)] = {
                          "channel_id": channel.id,
                          "joined_at": joined_at,
                          "last_tick": datetime.utcnow(),
                          "muted": member.voice.self_mute or member.voice.mute,
                          "deaf": member.voice.self_deaf or member.voice.deaf,
                          "bot_count": sum(1 for m in channel.members if m.bot),
                      }

                      # Zapisz last_voice_join do DB
                      await update_last_voice_join(guild.id, member.id, joined_at)
  ```

* Zaimplementuj event `on_voice_state_update`.

* Trzymaj w `active_sessions`:

  ```python
  active_sessions[(guild_id, user_id)] = {
      "channel_id": ...,
      "joined_at": datetime,
      "last_tick": datetime,
      "muted": bool,
      "deaf": bool,
      "bot_count": int,  # liczba botów w kanale (do ignore)
  }
  ```

* Scenariusze:

  * join → dodaj do mapy + zapisz `last_voice_join` do DB,
  * leave → **NAJPIERW** zapisz sesję (`save_session()`), **POTEM** usuń z mapy,
  * zmiana mute/deaf → aktualizuj flagi.

* **WAŻNE:** przy leave zawsze wywołaj `save_session()` przed `del active_sessions[...]`:

  ```python
  async def save_session(guild_id, user_id):
      session = active_sessions.get((guild_id, user_id))
      if not session:
          return

      # Oblicz ile czasu user był na voice
      duration = (datetime.utcnow() - session["last_tick"]).total_seconds()
      # Zapisz do DB (na razie tylko log)
      logger.info(f"Saving session: {user_id} was in voice for {duration}s")
  ```

* Dodaj background task (loop co 60s), który:

  * iteruje po `active_sessions`,
  * loguje: „Dodałbym XP user X”.

**Gotowe, gdy:** w konsoli widzisz poprawne logi przy wejściu/wyjściu i tickach.

---

### DAY08 – XP + levelowanie + zapis do DB

**Cel:** realne XP, realny ranking.

* Ustal na sztywno:

  * `XP_PER_MINUTE = 6`.

* Napisz helper:

  ```python
  def xp_needed_for_level(level: int) -> int:
      return 5 * (level ** 2) + 50 * level + 100
  ```

  *(Sprawdź wcześniej progresję: level 10 ≈ 3100 total XP ≈ 8.6h voice)*

* W ticku:

  * dla każdego usera:

    * sprawdź, czy kwalifikuje się do XP (na razie *bez* ignore solo/muted – to dodamy jutro).
    * dodaj 60s do `total_voice_sec`.
    * dodaj 6 XP do `total_xp` + `xp_into_level`.
    * sprawdź, czy `xp_into_level >= xp_needed_for_level(level)`:

      * jeśli tak → `level += 1`, `xp_into_level -= xp_needed`.
    * zapis do DB `upsert_user_stats(...)`.

* **NA KOŃCU** (dla każdego usera, któremu zaktualizowałeś stats):

  1. Pobierz `member` z `guild = bot.get_guild(guild_id)`, `guild.get_member(user_id)`.
  2. Weź `guild_roles_config = roles_config[guild_id]` (jeśli nie ma w configu – skip).
  3. Wywołaj:

     ```python
     await update_user_voice_role(member, guild_roles_config, total_voice_sec=stats.total_voice_sec)
     ```

* Sprawdź `/leaderboard` i `/rank` po kilku minutach siedzenia w voice.

**Gotowe, gdy:** siedząc na voice realnie rośniesz w rankingu **i dostajesz/tracisz role przy przekroczeniu progów**.

---

### DAY09 – Ignore solo/muted/AFK + sanity

**Cel:** anty-abuse i sensowna logika.

* Dodaj logikę anti-abuse:

  * ignorowanie kanału AFK (ID trzymany w configu / z API: `guild.afk_channel`),
  * jeśli user sam w kanale → nie naliczasz XP,
  * jeśli >50% ludzi w kanale to boty → nie naliczasz XP:

    ```python
    humans = [m for m in channel.members if not m.bot]
    bots = [m for m in channel.members if m.bot]
    if len(bots) >= len(humans):  # więcej/tyle samo botów co ludzi
        continue  # skip XP
    ```

  * jeśli muted/deaf (wg flag z voice state) → nie naliczasz XP,
  * *BONUS:* sprawdź `member.voice.self_stream` lub `self_video` - jeśli streamuje/ma kamerę, może dostać XP nawet solo (opcjonalne).
* Dodaj minimalne logowanie (np. log level DEBUG) kiedy user:

  * dostał XP,
  * został zignorowany (powód: solo/muted/afk).
* Szybki test: różne kombinacje – dwóch w pokoju, jeden, mute, itp.

**DODATKOWO:** Testuj zarządzanie rolami:

* user bez żadnego progu → nie ma ról,
* user spełnia pierwszy próg → dostaje najniższą rangę,
* user przekracza wyższy próg → stara ranga leci, nowa wpada,
* user schodzi z serwera → nic dramatycznego się nie dzieje (stats zostają w DB, Discord automatycznie zabiera role, tracking się zatrzymuje przy leave event).

* Dodaj **error handling dla role operations**:

  ```python
  try:
      await member.add_roles(...)
      await member.remove_roles(...)
  except discord.Forbidden:
      logger.error(f"Missing permissions to manage roles for {member}")
  except discord.HTTPException as e:
      logger.error(f"Failed to update roles: {e}")
  ```

* Dodaj w `config/roles_config.yaml` komentarze:

  ```yaml
  # config/roles_config.yaml
  guilds:
    "123456789012345678":  # Mój serwer
      tiers:
        # min_minutes = 0 -> rola startowa dla każdego, kto siedział kiedykolwiek
        - name: Rookie
          role_id: 111111111111111111
          min_minutes: 0
        # min_minutes = 300 -> 5h
        - name: Regular
          role_id: 222222222222222222
          min_minutes: 300
        ...
  ```

**Gotowe, gdy:** XP leci tylko tam, gdzie ma sens **i role są nadawane/zabierane poprawnie**.

---

## FAZA 3 – POLISH + DEVOPS (lokalnie)

### DAY10 – Prosty level-up log + config kanału

**Cel:** przygotowanie pod level-up message z konkretnym configiem.

* W miejscu, gdzie rośnie `level`, dodaj:

  * log: `user X leveled up to Y on guild Z`.
* Dodaj konfigurację w `config.py`:

  ```python
  LEVELUP_ANNOUNCE_ENABLED = False  # włącz w przyszłości
  LEVELUP_CHANNEL_ID = None  # None = wyślij DM do usera, albo ID kanału
  ```

* Zostaw TODO: implementacja wysyłania wiadomości (po DAY11).

**Gotowe, gdy:** w logach widzisz level-up'y i masz gotowy config na przyszłość.

---

### DAY10.5 – Admin commands + bonus utils

**Cel:** mieć narzędzia do ręcznej kontroli XP i debugowania + kalkulator poziomów.

* Dodaj komendy admin-only (sprawdzaj `interaction.user.guild_permissions.administrator`):

  * `/addxp @user amount` - ręczne dodanie/odjęcie XP (może być ujemne)

    * aktualizuj `total_xp`, przelicz `level` i `xp_into_level`
    * wywołaj `update_user_voice_role()` po zmianie
  * `/resetstats @user` - reset usera do 0 XP/level

    * ustaw wszystko na 0 w DB
    * zabierz wszystkie voice-tier role
  * `/syncvoice` - force rebuild `active_sessions` (jak coś się zepsuło)

    * uruchom tę samą logikę co `on_ready()`

* Dodaj ephemeral responses (tylko admin widzi):

  ```python
  await interaction.response.send_message("XP updated", ephemeral=True)
  ```

* **BONUS:** Dodaj `docs/level_calculator.py` - kalkulator progresji:

  ```python
  def xp_needed_for_level(level: int) -> int:
      return 5 * (level ** 2) + 50 * level + 100

  total = 0
  print("Level | Total XP | Hours (6XP/min)")
  print("-" * 40)
  for lvl in range(1, 51):
      need = xp_needed_for_level(lvl)
      total += need
      hours = total / 6 / 60
      if lvl % 5 == 0:  # co 5 leveli
          print(f"{lvl:5d} | {total:8,d} | {hours:6.1f}h")
  ```

  Przykładowe wyniki:
  - Level 10 → 3,100 XP → 8.6h
  - Level 20 → 13,100 XP → 36.4h
  - Level 50 → 85,100 XP → 236.4h (~10 dni non-stop)

**Gotowe, gdy:** możesz testować bot bez siedzenia godzinami na voice + masz kalkulator do tuningu XP.

---

### DAY11 – Dockerfile + docker-compose: full stack

**Cel:** 1 komenda startuje bota + bazę.

* Dodaj `Dockerfile` dla bota:

  * Python base image,
  * `pip install -r requirements.txt`,
  * `CMD ["python", "-m", "bot.main"]`.
* Rozszerz `docker-compose.yml`, żeby startował:

  * `db` (Postgres)
  * `bot` (z zależnością na `db`, env z `.env` / secrets).
* Sprawdź:

  * `docker-compose up` → bot się łączy, XP leci, ranking działa.

**Gotowe, gdy:** cały system (bot + DB) odpala się docker-compose i działa jak lokalne „mini-prod”.

---

### DAY12 – CI (GitHub Actions) – basic pipeline

**Cel:** automat do budowania obrazu i testów.

* Dodaj prosty `tests/`:

  * choćby unit test dla `xp_needed_for_level`.
* Workflow `.github/workflows/ci.yml`:

  * kroki:

    * checkout,
    * setup Python,
    * `pip install -r requirements.txt`,
    * `pytest` (nawet jeśli jest 1 test),
    * build Docker image (`docker build`).
* Opcja: push image do GHCR (kolejny plus DevOpsowy).

**Gotowe, gdy:** każdy push odpala CI, testy przechodzą, obraz się buduje.

---

## FAZA 4 – AWS / TERRAFORM (opcjonalna M2)

To możesz zrobić po Resilience-Lab albo jako M2 bota.

### DAY13 – Terraform: EC2 pod bota

**Cel:** minimalna infra pod bota.

* Terraform config:

  * VPC / subnet (możesz recyklingować z poprzednich projektów),
  * EC2 z Debianem,
  * Security Group:

    * SSH tylko z twojego IP,
  * output: public IP, itp.
* Na instancji:

  * zainstaluj Docker + docker-compose,
  * skopiuj `.env` (bez tokena do repo).

**Gotowe, gdy:** masz EC2 gotowe pod odpalenie docker-compose z botem.

---

### DAY14 – Deploy bota na EC2

**Cel:** bot działa 24/7 w AWS.

* Zrób:

  * `docker-compose.yml` na serwerze.
  * Odpal `docker-compose up -d`.
* Sprawdź:

  * bot odpowiada na `/ping`,
  * XP leci,
  * leaderboard żyje.

**Gotowe, gdy:** bot siedzi na EC2 i tyrka jak music bot kiedyś.

---

## Podsumowanie – co masz po tym planie

Po DAY01–DAY12:

* Realny, działający bot:

  * XP tylko za voice,
  * XP/level zapisane w Postgresie,
  * `/rank` + `/leaderboard` jako core,
  * **Automatyczne role „voice-tier" zależne od czasu na voice**, w pełni konfigurowalne z pliku,
  * ignore solo/muted/AFK,
  * Docker + docker-compose,
  * CI w GitHub Actions.

Po DAY13–DAY14:

* Bot stoi w AWS jako **żywy projekt DevOps/Cloud** w twoim portfolio.

---
