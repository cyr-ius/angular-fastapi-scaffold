# App

FastAPI backend serving an Angular frontend, shipped as one Docker image.

Template of [cyr-ius](https://github.com/cyr-ius) web applications: session
authentication (HttpOnly cookie), SQLite database with Alembic migrations, strict
security headers, unprivileged container, CI and releases through the reusable
workflows of [cyr-ius/.github](https://github.com/cyr-ius/.github).

## Run

```bash
docker compose up -d --build
docker compose logs app | grep -i password   # one-time admin password
```

Open <http://127.0.0.1:8000>. Behind plain HTTP (no TLS reverse proxy), set
`COOKIE_SECURE=false`, otherwise the browser does not send the session cookie back.

## Settings

| Variable                      | Default                  | Description                                     |
| ----------------------------- | ------------------------ | ----------------------------------------------- |
| `APP_NAME`                    | `App`                    | Name shown in the interface                     |
| `DATA_DIR`                    | `/var/lib/app`           | Database and generated secret key               |
| `DATABASE_URL`                | SQLite in `DATA_DIR`     | SQLAlchemy async URL                            |
| `SECRET_KEY`                  | generated in `DATA_DIR`  | Signs the session tokens                        |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480`                    | Session lifetime                                |
| `COOKIE_SECURE`               | `true`                   | Send the session cookie over HTTPS only         |
| `ADMIN_USERNAME`              | `admin`                  | Account created on the first start              |
| `SWAGGER_ENABLED`             | `false`                  | Interactive API documentation on `/api/docs`    |
| `LOG_LEVEL`                   | `INFO`                   | Python logging level                            |

## Development

See [AGENTS.md](AGENTS.md): commands, checks, structure and security invariants.

## License

[MIT](LICENSE)
