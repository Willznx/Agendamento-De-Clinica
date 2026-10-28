"""Teste de fumaça da interface: cada página abre sem erro."""
# "Teste de fumaça" (smoke test) é uma checagem rápida e superficial: não verifica
# se os resultados estão certos, só se o app roda sem quebrar.
import pytest
# AppTest permite executar o app Streamlit sem abrir navegador, simulando cliques e seleções
from streamlit.testing.v1 import AppTest
import db


# autouse=True: esta fixture roda automaticamente antes de cada teste, sem precisar ser chamada.
# A intenção é apontar o app para um banco temporário (tmp_path é uma pasta descartável do pytest),
# para o teste não mexer no clinica.db real. O monkeypatch desfaz a alteração ao fim de cada teste.
@pytest.fixture(autouse=True)
def banco(tmp_path, monkeypatch):
    monkeypatch.setenv("CLINICA_DB", str(tmp_path / "ui.db"))


# parametrize: o mesmo teste roda uma vez para cada página da lista abaixo.
# Os textos precisam ser idênticos aos rótulos do menu lateral do app.py.
@pytest.mark.parametrize("pagina", [
    "📅 Agenda do dia", "➕ Novo agendamento", "👤 Pacientes", "🩺 Profissionais", "📊 Relatórios",
])
def test_paginas_abrem(pagina):
    # Carrega o app.py e executa o script uma primeira vez (abre na página inicial);
    # default_timeout=15 dá até 15 segundos para a execução terminar
    at = AppTest.from_file("app.py", default_timeout=15).run()
    # Seleciona a página no radio da barra lateral (o primeiro radio é o menu) e executa de novo
    at.sidebar.radio[0].set_value(pagina).run()
    # O teste passa se a página rodou sem lançar nenhuma exceção; se falhar,
    # o assert mostra a exceção capturada na mensagem de erro
    assert not at.exception, at.exception
