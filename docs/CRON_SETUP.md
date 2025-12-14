# Configuration CRON pour le Crawler Winners

Le crawler des winners doit s'exécuter toutes les 6 heures pour mettre à jour automatiquement le catalog.

## Option 1: CRON Linux/Mac

Ajouter dans votre crontab (`crontab -e`):

```bash
# Crawler les winners toutes les 6 heures
0 */6 * * * cd /chemin/vers/marketpulse-africa/scraper && /usr/bin/python3 cron_worker.py >> /var/log/marketpulse_cron.log 2>&1
```

## Option 2: Systemd Timer (Linux)

Créer `/etc/systemd/system/marketpulse-winners-crawler.service`:

```ini
[Unit]
Description=MarketPulse Winners Crawler
After=network.target

[Service]
Type=oneshot
User=marketpulse
WorkingDirectory=/chemin/vers/marketpulse-africa/scraper
Environment="DATABASE_URL=postgresql://marketpulse:marketpulse_password@localhost:5432/marketpulse"
ExecStart=/usr/bin/python3 cron_worker.py
```

Créer `/etc/systemd/system/marketpulse-winners-crawler.timer`:

```ini
[Unit]
Description=Run MarketPulse Winners Crawler every 6 hours

[Timer]
OnBootSec=10min
OnUnitActiveSec=6h
Unit=marketpulse-winners-crawler.service

[Install]
WantedBy=timers.target
```

Activer le timer:
```bash
sudo systemctl enable marketpulse-winners-crawler.timer
sudo systemctl start marketpulse-winners-crawler.timer
```

## Option 3: Docker avec CRON

Ajouter dans `docker-compose.yml`:

```yaml
  cron_crawler:
    build:
      context: ./scraper
      dockerfile: Dockerfile
    container_name: marketpulse_cron_crawler
    environment:
      REDIS_URL: redis://redis:6379/0
      DATABASE_URL: postgresql://marketpulse:marketpulse_password@postgres:5432/marketpulse
    volumes:
      - ./scraper:/app
    command: >
      sh -c "
        echo '0 */6 * * * cd /app && python cron_worker.py >> /var/log/cron.log 2>&1' | crontab - &&
        crond -f
      "
    depends_on:
      - postgres
      - redis
```

## Option 4: Python Schedule (Développement)

Pour tester localement, créer `scraper/test_cron.py`:

```python
import schedule
import time
from cron_worker import main

schedule.every(6).hours.do(main)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## Vérification

Vérifier que le crawler fonctionne:

```bash
# Test manuel
cd scraper
python cron_worker.py

# Vérifier les logs
tail -f /var/log/marketpulse_cron.log
```





Le crawler des winners doit s'exécuter toutes les 6 heures pour mettre à jour automatiquement le catalog.

## Option 1: CRON Linux/Mac

Ajouter dans votre crontab (`crontab -e`):

```bash
# Crawler les winners toutes les 6 heures
0 */6 * * * cd /chemin/vers/marketpulse-africa/scraper && /usr/bin/python3 cron_worker.py >> /var/log/marketpulse_cron.log 2>&1
```

## Option 2: Systemd Timer (Linux)

Créer `/etc/systemd/system/marketpulse-winners-crawler.service`:

```ini
[Unit]
Description=MarketPulse Winners Crawler
After=network.target

[Service]
Type=oneshot
User=marketpulse
WorkingDirectory=/chemin/vers/marketpulse-africa/scraper
Environment="DATABASE_URL=postgresql://marketpulse:marketpulse_password@localhost:5432/marketpulse"
ExecStart=/usr/bin/python3 cron_worker.py
```

Créer `/etc/systemd/system/marketpulse-winners-crawler.timer`:

```ini
[Unit]
Description=Run MarketPulse Winners Crawler every 6 hours

[Timer]
OnBootSec=10min
OnUnitActiveSec=6h
Unit=marketpulse-winners-crawler.service

[Install]
WantedBy=timers.target
```

Activer le timer:
```bash
sudo systemctl enable marketpulse-winners-crawler.timer
sudo systemctl start marketpulse-winners-crawler.timer
```

## Option 3: Docker avec CRON

Ajouter dans `docker-compose.yml`:

```yaml
  cron_crawler:
    build:
      context: ./scraper
      dockerfile: Dockerfile
    container_name: marketpulse_cron_crawler
    environment:
      REDIS_URL: redis://redis:6379/0
      DATABASE_URL: postgresql://marketpulse:marketpulse_password@postgres:5432/marketpulse
    volumes:
      - ./scraper:/app
    command: >
      sh -c "
        echo '0 */6 * * * cd /app && python cron_worker.py >> /var/log/cron.log 2>&1' | crontab - &&
        crond -f
      "
    depends_on:
      - postgres
      - redis
```

## Option 4: Python Schedule (Développement)

Pour tester localement, créer `scraper/test_cron.py`:

```python
import schedule
import time
from cron_worker import main

schedule.every(6).hours.do(main)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## Vérification

Vérifier que le crawler fonctionne:

```bash
# Test manuel
cd scraper
python cron_worker.py

# Vérifier les logs
tail -f /var/log/marketpulse_cron.log
```



