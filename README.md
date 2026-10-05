

## Testing 

```bash
docker compose up --build -d
python3 scripts/initialize.py
python3 scripts/role_testing.py
docker compose down -v
```

```bash
docker compose up --build -d
python3 scripts/initialize.py
```

## Deployment

```bash
docker compose up --build -d
python3 scripts/initialize.py --admin-only
```