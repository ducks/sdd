{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  packages = [ (pkgs.python312.withPackages (ps: [ ps.prometheus-client ps.flask ps.pyyaml ])) pkgs.docker pkgs.docker-compose ];
}
