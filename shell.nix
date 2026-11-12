{ pkgs ? import (builtins.fetchTarball {
    url = "https://github.com/NixOS/nixpkgs/archive/9fbb54b33e91ee4ca368e35a78e0613c720600b3.tar.gz";
    sha256 = "sha256-cV5xEJJK3BvhU8rEd4mC9UsmDi5qscv/kzGPhBRC5WA=";
  }) {} }:
pkgs.mkShell {
  packages = [ (pkgs.python312.withPackages (ps: [ ps.prometheus-client ps.flask ps.pyyaml ])) pkgs.docker pkgs.docker-compose pkgs.docker-buildx pkgs.ruff pkgs.rustc pkgs.cargo pkgs.rustfmt pkgs.clippy pkgs.gnumake pkgs.git pkgs.stdenv.cc ];
  # Opt-in public-fixture Docker environment: do not alter the user's credentials
  # or plugin configuration. A newer client must use matching Nix plugins.
  shellHook = ''
    if [ "''${SDD_ISOLATED_DOCKER:-0}" = 1 ]; then
      sdd_docker_config=$(mktemp -d "''${TMPDIR:-/tmp}/sdd-docker.XXXXXXXX")
      export DOCKER_CONFIG="$sdd_docker_config"
      cat > "$DOCKER_CONFIG/config.json" <<'JSON'
${builtins.toJSON { cliPluginsExtraDirs = [
  "${pkgs.docker-buildx}/libexec/docker/cli-plugins"
  "${pkgs.docker-compose}/libexec/docker/cli-plugins"
]; }}
JSON
      trap 'rm -rf -- "$sdd_docker_config"' EXIT
    fi
  '';
}
