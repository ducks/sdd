# Local interview preparation

The supplied environment is Neovim + Python + Claude Code CLI. Before the interview,
confirm with ICEYE that this is acceptable despite a VS Code setup checklist.
Verify Google Meet screen sharing in Chrome on the actual Wayland/Hyprland session;
launching the browser alone does not establish that sharing works. This checklist
is based on the user's notes, not independently confirmed interview policy.

Check tools manually in the chosen environment:

```sh
nvim --version | head -1
claude --version
python3 --version
uv --version
docker --version
docker compose version
git --version
make --version
```

Use the repository's Nix shell if appropriate rather than installing tools globally.
Check Python is 3.12+ and the repository's documented uv/test commands work.
Verify Docker daemon access and Compose support without altering user settings.
Do not print tokens or share credential files during a screen share.

Optional pre-pulls from the supplied checklist, requiring network/container
authorization (never run automatically during skill discovery):

```sh
docker pull prom/prometheus:latest
docker pull grafana/grafana:latest
docker pull python:3.12-slim
```

Latest tags are convenience cache warming, not reproducible image pins. If the
exercise supplies image versions/digests, use those instead. Do not replace the
provided Compose stack, expose admin services or add services that are not needed.
These steps do not prove the exercise's tests, metrics or service behavior work;
CODE's evaluation phase must demonstrate them on the actual repository.
