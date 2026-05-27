"""
Punto de entrada en la raiz del proyecto: delega en src/app.py
para que `streamlit run app.py` desde esta carpeta cargue la app con secciones.
"""
from pathlib import Path
import os
import sys

_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"
os.chdir(_SRC)
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

_APP = _SRC / "app.py"
_globals = {
    "__name__": "__main__",
    "__file__": str(_APP),
    "__doc__": None,
    "__package__": None,
    "__loader__": None,
    "__spec__": None,
}
with open(_APP, encoding="utf-8") as f:
    exec(compile(f.read(), str(_APP), "exec"), _globals)
