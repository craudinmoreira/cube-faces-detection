"""Versão do projeto, lida do pyproject.toml (atualizado pelo release-please)."""

import tomllib
from pathlib import Path

PYPROJECT = Path(__file__).resolve().with_name('pyproject.toml')


def get_version(pyproject=PYPROJECT):
    try:
        with open(pyproject, 'rb') as file:
            return tomllib.load(file)['project']['version']
    except (OSError, KeyError, tomllib.TOMLDecodeError):
        return 'desconhecida'
