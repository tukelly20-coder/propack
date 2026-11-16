# Chạy Propack bằng Docker

## Lần đầu trên mỗi máy

Nếu `docker compose` chưa có:

```bash
sudo apt update
sudo apt install -y docker-compose-v2
```

Nếu chạy Docker bị lỗi `permission denied while trying to connect to the docker API`:

```bash
sudo usermod -aG docker "$USER"
newgrp docker
```

Nếu vẫn lỗi sau `newgrp docker`, đăng xuất rồi đăng nhập lại máy.

```bash
docker compose build
docker compose up -d
```

Mở web:

```text
http://localhost:8001
```

Server cũng mở cổng socket cũ:

```text
12345
```

## Xem log

```bash
docker compose logs -f
```

## Tắt server

```bash
docker compose down
```

## Chạy khi chưa sửa quyền Docker

Nếu chưa thêm user vào group `docker`, có thể chạy tạm bằng `sudo`:

```bash
sudo docker build -t propack-server .
sudo docker rm -f propack-server 2>/dev/null || true
sudo docker run -d \
  --name propack-server \
  --restart unless-stopped \
  -p 8001:8001 \
  -p 12345:12345 \
  -v "$PWD/DB.db:/app/DB.db" \
  -v "$PWD/used_codes.json:/app/used_codes.json" \
  -v "$PWD/web_sessions.json:/app/web_sessions.json" \
  -v "$PWD/credentials.json:/app/credentials.json" \
  -v "$PWD/system_prompt.json:/app/system_prompt.json" \
  -v "$PWD/misc/fallback_excel:/app/misc/fallback_excel" \
  propack-server
```

Xem log khi chạy bằng `sudo docker run`:

```bash
sudo docker logs -f propack-server
```

## Dữ liệu

Các file dưới đây được mount từ thư mục project trên máy host vào container, nên rebuild image không làm mất dữ liệu:

- `DB.db`
- `used_codes.json`
- `web_sessions.json`
- `credentials.json`
- `system_prompt.json`
- `misc/fallback_excel/`

Khi copy sang máy khác, copy kèm các file dữ liệu này nếu muốn giữ dữ liệu hiện tại.
