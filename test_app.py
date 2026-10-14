"""Teste de fumaça da interface: cada página abre sem erro."""
import pytest
from streamlit.testing.v1 import AppTest
import db


@pytest.fixture(autouse=True)
def banco(tmp_path, monkeypatch):
    monkeypatch.setenv("CLINICA_DB", str(tmp_path / "ui.db"))


@pytest.mark.parametrize("pagina", [
    "📅 Agenda do dia", "➕ Novo agendamento", "👤 Pacientes", "🩺 Profissionais", "📊 Relatórios",
])
def test_paginas_abrem(pagina):
    at = AppTest.from_file("app.py", default_timeout=15).run()
    at.sidebar.radio[0].set_value(pagina).run()
    assert not at.exception, at.exception
