"""Nenhuma SQL do motor é montada por interpolação de string."""

import ast
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
MODULOS_SQL = (
    RAIZ / "src" / "logidash" / "metrics" / "compilador.py",
    RAIZ / "src" / "logidash" / "metrics" / "guardiao_sql.py",
    RAIZ / "src" / "logidash" / "metrics" / "executor_duckdb.py",
)
_PALAVRAS_SQL = ("SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "MERGE")


def test_modulos_de_sql_nao_interpolam() -> None:
    for caminho in MODULOS_SQL:
        arvore = ast.parse(caminho.read_text(encoding="utf-8"))
        for no in ast.walk(arvore):
            assert not isinstance(no, ast.JoinedStr), caminho.name
            if isinstance(no, ast.BinOp):
                assert not isinstance(no.op, ast.Mod), caminho.name
            if isinstance(no, ast.Call) and isinstance(no.func, ast.Attribute):
                assert no.func.attr != "format", caminho.name
            if isinstance(no, ast.Call) and isinstance(no.func, ast.Name):
                assert no.func.id not in {"eval", "exec"}, caminho.name


def test_fstring_nao_carrega_comando_sql() -> None:
    pacote = RAIZ / "src" / "logidash"
    for caminho in pacote.rglob("*.py"):
        arvore = ast.parse(caminho.read_text(encoding="utf-8"))
        for no in ast.walk(arvore):
            if not isinstance(no, ast.JoinedStr):
                continue
            for parte in no.values:
                if isinstance(parte, ast.Constant) and isinstance(parte.value, str):
                    maiusculas = parte.value.upper()
                    for palavra in _PALAVRAS_SQL:
                        assert palavra not in maiusculas, caminho.name


def test_compilador_e_executor_nao_tem_sql_literal() -> None:
    for nome in ("compilador.py", "executor_duckdb.py"):
        texto = (RAIZ / "src" / "logidash" / "metrics" / nome).read_text(encoding="utf-8").upper()
        for palavra in ("SELECT ", "INSERT ", "DELETE ", "DROP TABLE", "UPDATE "):
            assert palavra not in texto
