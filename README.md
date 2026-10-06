

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

Enable the Public Frontend (Funnel): Run this command to map the public HTTPS port 443 to Nginx's public listener on port 80.
```bash
docker exec tailscale_gateway tailscale funnel --bg --https=443 http://nginx:80
```
Enable the Private Backend (Serve): Run this command to map the private Tailnet HTTPS port 8443 to Nginx's private listener on port 81.
```bash
docker exec tailscale_gateway tailscale serve --bg --https=8443 http://nginx:81
```