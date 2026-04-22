import re
import sys
from pathlib import Path


PYPROJECT = Path("pyproject.toml")


def get_current_version() -> str:
    content = PYPROJECT.read_text(encoding="utf-8")
    match = re.search(r'version\s*=\s*"(\d+)\.(\d+)\.(\d+)"', content)
    if not match:
        raise RuntimeError("Não foi possível localizar a versão no pyproject.toml")
    return ".".join(match.groups())


def bump_patch(version: str) -> str:
    major, minor, patch = map(int, version.split("."))
    return f"{major}.{minor}.{patch + 1}"


def set_version(new_version: str) -> None:
    content = PYPROJECT.read_text(encoding="utf-8")
    updated = re.sub(
        r'version\s*=\s*"\d+\.\d+\.\d+"',
        f'version = "{new_version}"',
        content,
        count=1,
    )
    PYPROJECT.write_text(updated, encoding="utf-8")


def main():
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python release_version.py current")
        print("  python release_version.py next")
        print("  python release_version.py set 0.1.6")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "current":
        print(get_current_version())
        return

    if command == "next":
        print(bump_patch(get_current_version()))
        return

    if command == "set":
        if len(sys.argv) != 3:
            raise RuntimeError("Informe a nova versão. Ex: python release_version.py set 0.1.6")
        set_version(sys.argv[2])
        print(sys.argv[2])
        return

    raise RuntimeError(f"Comando inválido: {command}")


if __name__ == "__main__":
    main()