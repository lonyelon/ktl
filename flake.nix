{
  description = "KTL Query — backend module and CLI tool for kettlebell tracking";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }: let
    system = "x86_64-linux";
    pkgs = import nixpkgs { inherit system; };
    python = pkgs.python3;
  in {
    packages."x86_64-linux".ktl-query = python.pkgs.buildPythonApplication {
      pname = "ktl-query";
      version = "1.0.0";
      src = ./ktl-query;
      format = "pyproject";
      propagatedBuildInputs = with python.pkgs; [ pyyaml ];
      nativeBuildInputs = [ python.pkgs.setuptools ];
    };

    packages."x86_64-linux".ktl-web = python.pkgs.buildPythonApplication {
      pname = "ktl-web";
      version = "1.0.0";
      src = ./.;

      # Add Python deps here if needed
      propagatedBuildInputs = with python.pkgs; [
        flask
        numpy
        watchdog
        self.packages.${system}.ktl-query
      ];

      format = "other";
      installPhase = ''
        mkdir -p $out/bin
        cp -r ktl-web/* $out/bin/
        chmod +x $out/bin/ktl-web
      '';
    };

    devShells.${system}.default = pkgs.mkShell {
      packages = [
        pkgs.python3
        python.pkgs.flask
        python.pkgs.numpy
        python.pkgs.pyyaml
        python.pkgs.watchdog
        (self.packages.${system}.ktl-query)
      ];
    };
  };
}
