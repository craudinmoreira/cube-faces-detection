import pytest


@pytest.fixture(autouse=True)
def isolated_cwd(tmp_path, monkeypatch):
    """Roda cada teste num diretório vazio.

    O app lê e grava `calibration.json` no diretório atual. Sem isso, os testes
    passariam a depender da calibração local de quem os roda.
    """
    monkeypatch.chdir(tmp_path)
