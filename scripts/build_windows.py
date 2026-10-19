"""Build automatizado do ZIP Windows. Execute a partir da raiz do projeto."""
import importlib.metadata
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def build():
    if sys.platform != "win32":
        raise SystemExit("Gere o .exe no Windows. O PyInstaller não faz compilação cruzada.")
    subprocess.run([
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile",
        "--windowed", "--name", "WordsAtack", "--icon", "NONE",
        "--collect-data", "pygame", "--paths", str(ROOT),
        "--distpath", str(ROOT / "dist"), "--workpath", str(ROOT / "build"),
        "--specpath", str(ROOT / "build"), str(ROOT / "run_game.py"),
    ], cwd=ROOT, check=True)
    notices = ROOT / "build" / "licenses"
    notices.mkdir(parents=True, exist_ok=True)
    distribution = importlib.metadata.distribution("pygame-ce")
    for item in distribution.files or []:
        if any(term in str(item).lower() for term in ("license", "copying", "lgpl")):
            source = Path(distribution.locate_file(item))
            if source.is_file():
                # Nome do caminho distingue licenças homônimas.
                destination = notices / (str(item).replace("/", "_").replace("\\", "_"))
                shutil.copy2(source, destination)
    python_license = Path(sys.base_prefix) / "LICENSE.txt"
    if python_license.exists():
        shutil.copy2(python_license, notices / "PYTHON-LICENSE.txt")
    archive = ROOT / "dist" / "WordsAtack-Windows.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        bundle.write(ROOT / "dist" / "WordsAtack.exe", "WordsAtack.exe")
        bundle.write(ROOT / "LEIA-ME-JOGADOR.txt", "LEIA-ME.txt")
        bundle.write(ROOT / "THIRD_PARTY.md", "THIRD_PARTY.md")
        for source in notices.iterdir():
            bundle.write(source, "licenses/" + source.name)
    print(f"Pronto: {archive}")


if __name__ == "__main__":
    build()
