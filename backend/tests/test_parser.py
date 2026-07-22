from pathlib import Path

from app.models.repository import Repository
from app.services.scanner.scanner_service import RepositoryScanner
from app.services.parser.ParserService import ParserService


GOOD = '''\
import os
from collections import OrderedDict


class Base:
    pass


class Service(Base):
    @staticmethod
    def run(self, x):
        return os.getcwd()


def helper(a, b):
    return Service().run(a)
'''


def _parse(tmp_path: Path) -> Repository:
    repo = Repository(name="t", github_url="local://t", local_path=str(tmp_path))
    repo = RepositoryScanner().scan(repo)
    return ParserService().parse(repo)


def _file(repo, name):
    return next(f for f in repo.files if f.name == name)


def test_extracts_imports_classes_functions(tmp_path):
    (tmp_path / "good.py").write_text(GOOD)
    repo = _parse(tmp_path)

    f = _file(repo, "good.py")
    imports = [i.module for i in f.imports]
    assert "os" in imports
    assert "collections.OrderedDict" in imports

    class_names = [c.name for c in f.classes]
    assert {"Base", "Service"} <= set(class_names)

    service = next(c for c in f.classes if c.name == "Service")
    assert "Base" in service.base_classes

    method_names = [m.name for m in service.methods]
    assert "run" in method_names

    run = next(m for m in service.methods if m.name == "run")
    assert [p.name for p in run.parameters] == ["self", "x"]
    assert "staticmethod" in run.decorators
    assert "getcwd" in [c.name for c in run.calls]

    helper = next(fn for fn in f.functions if fn.name == "helper")
    assert [p.name for p in helper.parameters] == ["a", "b"]
    call_names = [c.name for c in helper.calls]
    assert "run" in call_names and "Service" in call_names


def test_skips_unparseable_file_without_crashing(tmp_path):
    (tmp_path / "good.py").write_text(GOOD)
    (tmp_path / "bad.py").write_text("lazy import re\n")          # invalid syntax
    (tmp_path / "bin.py").write_bytes(b"\xff\xfe\x00 not utf-8")   # bad encoding

    repo = _parse(tmp_path)  # must not raise

    bad = _file(repo, "bad.py")
    assert bad.parse_error is not None
    assert bad.classes == [] and bad.functions == []

    good = _file(repo, "good.py")
    assert good.parse_error is None
    assert good.classes  # still parsed the valid file
