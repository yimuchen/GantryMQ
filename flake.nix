{
  description = "Configuration to testing Gantry MQ";

  inputs = {
    # Specify the source of Home Manager and Nixpkgs.
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs, ... }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in {
      defaultPackage.${system} = pkgs.python3;

      # Adding shell that is required for developement using editors, this is
      # mainly to include additional language servers and formatters that are
      # not listed for interactive use.
      devShells.${system} = {
        default = pkgs.mkShell {
          name = "Environment for editing";
          packages = [
            pkgs.cmake
            pkgs.clangd # C++ language server
            pkgs.ruff # python formatter server
            (pkgs.python3.withPackages (ps: [
              ps.python-lsp-server # Language servers
              ps.pyvisa # Listing all python dependencies to get full auto complete
              ps.pyzmq
              ps.opencv4
            ]))

          ];
        };
        server = pkgs.mkShell {
          name = "Environment for server side code";
          packages = [
            # C++ related tools
            pkgs.cmake
            pkgs.gcc

            # Python language tools
            (pkgs.python3.withPackages (ps: [ ps.pyvisa ps.pyzmq ps.opencv4 ]))
          ];
        };
        client = pkgs.mkShell {
          name = "Environment for client side code";
          packages = [ (pkgs.python3.withPackages (ps: [ ps.pyzmq ])) ];
        };
      };
    };
}
