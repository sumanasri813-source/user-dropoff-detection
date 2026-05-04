Systemd Deployment

Place the service file at /etc/systemd/system/user-dropoff-detection.service (update paths first).

Ensure the `WorkingDirectory` and `ExecStart` paths in the service file point to the repository root and `startup/run.sh` respectively.

Provide secrets using an `EnvironmentFile` or your platform's secret manager. Example `/etc/user-dropoff.env`:

SESSION_SECRET_KEY=REPLACE_ME
JWT_SECRET_KEY=REPLACE_ME

Example commands:

```bash
sudo cp startup/systemd/user-dropoff-detection.service /etc/systemd/system/user-dropoff-detection.service
sudo cp /path/to/user-dropoff.env /etc/user-dropoff.env
sudo systemctl daemon-reload
sudo systemctl enable --now user-dropoff-detection
sudo journalctl -u user-dropoff-detection -f
```

Notes:

- The startup script uses `gunicorn` — ensure it is installed in the environment used by the service.
- Keep secrets out of the unit file. Use `EnvironmentFile` with proper file permissions (600), or integrate with your secrets manager.
