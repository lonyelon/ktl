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

    packages."x86_64-linux".ktl = python.pkgs.buildPythonApplication {
      pname = "ktl";
      version = "1.0.0";
      src = ./.;

      # Add Python deps here if needed
      propagatedBuildInputs = with python.pkgs; [
        pyyaml
        self.packages.${system}.ktl-query
      ];

      format = "other";
      installPhase = ''
        mkdir -p $out/bin
        cp ktl $out/bin
        chmod +x $out/bin/ktl
      '';
    };

    devShells.${system}.default = pkgs.mkShell {
      packages = [ python (self.packages.${system}.default) ];
    };
  };
}
