import pytest
import db


@pytest.fixture(autouse=True)
def banco_temporario(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "teste.db"))
    db.init_db()


@pytest.fixture
def base():
    p1 = db.criar_paciente("Ana Souza", "(86) 99999-1111")
    p2 = db.criar_paciente("João Lima", "86988882222")
    d1 = db.criar_profissional("Dra. Marta", "Clínica geral")
    d2 = db.criar_profissional("Dr. Paulo", "Pediatria")
    return p1, p2, d1, d2


def test_paciente_valida_telefone():
    with pytest.raises(db.ErroDeNegocio):
        db.criar_paciente("Ana", "123")


def test_paciente_valida_nome():
    with pytest.raises(db.ErroDeNegocio):
        db.criar_paciente(" ", "86999991111")


def test_telefone_e_normalizado():
    pid = db.criar_paciente("Ana", "(86) 99999-1111")
    assert db.listar_pacientes()[0]["telefone"] == "86999991111"


def test_agendar_e_listar(base):
    p1, _, d1, _ = base
    db.agendar(p1, d1, "2026-10-01 09:00", "Consulta")
    ag = db.listar_agenda("2026-10-01")
    assert len(ag) == 1 and ag[0]["paciente"] == "Ana Souza"


def test_bloqueia_mesmo_profissional_mesmo_horario(base):
    p1, p2, d1, _ = base
    db.agendar(p1, d1, "2026-10-01 09:00", "Consulta")
    with pytest.raises(db.ErroDeNegocio, match="indisponível"):
        db.agendar(p2, d1, "2026-10-01 09:00", "Retorno")


def test_bloqueia_paciente_em_dois_lugares(base):
    p1, _, d1, d2 = base
    db.agendar(p1, d1, "2026-10-01 09:00", "Consulta")
    with pytest.raises(db.ErroDeNegocio, match="outro atendimento"):
        db.agendar(p1, d2, "2026-10-01 09:00", "Consulta")


def test_cancelado_libera_horario(base):
    p1, p2, d1, _ = base
    a = db.agendar(p1, d1, "2026-10-01 09:00", "Consulta")
    db.alterar_situacao(a, "cancelado")
    db.agendar(p2, d1, "2026-10-01 09:00", "Retorno")  # não deve falhar


def test_reativar_cancelado_com_horario_ocupado_falha(base):
    p1, p2, d1, _ = base
    a = db.agendar(p1, d1, "2026-10-01 09:00", "Consulta")
    db.alterar_situacao(a, "cancelado")
    db.agendar(p2, d1, "2026-10-01 09:00", "Retorno")
    with pytest.raises(db.ErroDeNegocio):
        db.alterar_situacao(a, "agendado")


def test_reagendar(base):
    p1, _, d1, _ = base
    a = db.agendar(p1, d1, "2026-10-01 09:00", "Consulta")
    db.reagendar(a, "2026-10-02 10:30")
    assert db.obter_atendimento(a)["data_hora"] == "2026-10-02 10:30"


def test_reagendar_para_horario_ocupado_falha(base):
    p1, p2, d1, _ = base
    db.agendar(p1, d1, "2026-10-01 09:00", "Consulta")
    b = db.agendar(p2, d1, "2026-10-01 09:30", "Consulta")
    with pytest.raises(db.ErroDeNegocio):
        db.reagendar(b, "2026-10-01 09:00")


def test_reagendar_para_o_mesmo_horario_nao_conflita_consigo(base):
    p1, _, d1, _ = base
    a = db.agendar(p1, d1, "2026-10-01 09:00", "Consulta")
    db.reagendar(a, "2026-10-01 09:00")


def test_situacao_invalida(base):
    p1, _, d1, _ = base
    a = db.agendar(p1, d1, "2026-10-01 09:00", "Consulta")
    with pytest.raises(db.ErroDeNegocio):
        db.alterar_situacao(a, "qualquer")


def test_nao_exclui_paciente_com_historico(base):
    p1, _, d1, _ = base
    db.agendar(p1, d1, "2026-10-01 09:00", "Consulta")
    with pytest.raises(db.ErroDeNegocio):
        db.excluir_paciente(p1)


def test_exclui_paciente_sem_historico(base):
    _, p2, _, _ = base
    db.excluir_paciente(p2)
    assert all(p["id"] != p2 for p in db.listar_pacientes())


def test_excluir_atendimento(base):
    p1, _, d1, _ = base
    a = db.agendar(p1, d1, "2026-10-01 09:00", "Consulta")
    db.excluir_atendimento(a)
    assert db.obter_atendimento(a) is None


def test_horarios_livres(base):
    p1, _, d1, _ = base
    db.agendar(p1, d1, "2026-10-01 09:00", "Consulta")
    livres = db.horarios_livres("2026-10-01", d1, ["08:30", "09:00", "09:30"])
    assert livres == ["08:30", "09:30"]


def test_busca_paciente_e_sql_injection(base):
    assert len(db.listar_pacientes("Ana")) == 1
    assert db.listar_pacientes("'; DROP TABLE pacientes;--") == []
    assert len(db.listar_pacientes()) == 2


def test_relatorios(base):
    p1, p2, d1, _ = base
    a = db.agendar(p1, d1, "2026-10-01 09:00", "Consulta")
    b = db.agendar(p2, d1, "2026-10-01 09:30", "Consulta")
    db.alterar_situacao(a, "falta")
    db.alterar_situacao(b, "realizado")
    r = {x["situacao"]: x["total"] for x in db.resumo_por_situacao("2026-10-01", "2026-10-01")}
    assert r == {"falta": 1, "realizado": 1}
    f = db.faltas_por_profissional("2026-10-01", "2026-10-01")
    assert f[0]["faltas"] == 1
