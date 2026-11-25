from version import PYPROJECT, get_version


def test_reads_the_project_version():
    assert get_version() == get_version(PYPROJECT) != 'desconhecida'


def test_unknown_when_pyproject_is_missing_or_invalid(tmp_path):
    assert get_version(tmp_path / 'missing.toml') == 'desconhecida'
    broken = tmp_path / 'pyproject.toml'
    broken.write_text('[project]\nname = "x"\n', encoding='utf-8')
    assert get_version(broken) == 'desconhecida'


def test_main_prints_the_version():
    import subprocess
    import sys
    from pathlib import Path

    main = Path(__file__).resolve().parent.parent / 'main.py'
    result = subprocess.run(  # noqa: S603 - executa o próprio main.py com o Python atual
        [sys.executable, str(main), '--version'], capture_output=True, text=True, check=True
    )

    assert result.stdout.strip() == f'main.py {get_version()}'
