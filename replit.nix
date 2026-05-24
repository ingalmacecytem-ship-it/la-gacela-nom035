{ pkgs }:
{
  deps = [
    pkgs.python310Full
    pkgs.python310Packages.pip
  ];
  shellHook = ''
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
  '';
}
