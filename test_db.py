# Testes automatizados da camada de dados (db.py): validações, regras de agendamento,
# conflitos de horário, exclusões e relatórios. Rodar com:  pytest
import pytest
import db


# autouse=True: roda antes de cada teste, automaticamente.
# Aqui o isolamento funciona: o monkeypatch troca db.DB_PATH diretamente (o atributo do módulo
# já importado) por um arquivo temporário, então os testes nunca tocam no clinica.db real.
# Cada teste começa com um banco novo e vazio, e o monkeypatch desfaz a troca ao final.
@pytest.fixture(autouse=True)
def banco_temporario(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "teste.db"))
    db.init_db()


# Fixture de apoio: cria 2 pacientes e 2 profissionais e devolve os ids.
# Só roda nos testes que a pedem como parâmetro (os que recebem "base").
# O segundo telefone está sem máscara de propósito, para testar os dois formatos.
@pytest.fixture
def base():
    p1 = db.criar_paciente("Ana Souza", "(86) 99999-1111")
    p2 = db.criar_paciente("João Lima", "86988882222")
    d1 = db.criar_profissional("Dra. Marta", "Clínica geral")
    d2 = db.criar_profissional("Dr. Paulo", "Pediatria")
    return p1, p2, d1, d2


# ------------------------------------------------------------ validações
# Telefone com poucos dígitos deve ser recusado com ErroDeNegocio
def test_paciente_valida_telefone():
    with pytest.raises(db.ErroDeNegocio):
        db.criar_paciente("Ana", "123")


# Nome só com espaço fica vazio depois do strip() e deve ser recusado
def test_paciente_valida_nome():
    with pytest.raises(db.ErroDeNegocio):
        db.criar_paciente(" ", "86999991111")


# O telefone digitado com máscara deve ser salvo só com dígitos
def test_telefone_e_normalizado():
    pid = db.criar_paciente("Ana", "(86) 99999-1111")
    assert db.listar_pacientes()[0]["telefone"] == "86999991111"


# ------------------------------------------------------------ agendamento
# Caminho feliz: agenda um atendimento e confere que aparece na agenda do dia,
# com o nome do paciente vindo do JOIN
def test_agendar_e_listar(base):
    p1, _, d1, _ = base
    db.agendar(p1, d1, "2026-10-01 09:00", "Consulta")
    ag = db.listar_agenda("2026-10-01")
    assert len(ag) == 1 and ag[0]["paciente"] == "Ana Souza"


# Regra 1: o mesmo profissional não pode ter dois pacientes no mesmo horário.
# O "match" confere que a mensagem de erro contém a palavra esperada.
def test_bloqueia_mesmo_profissional_mesmo_horario(base):
    p1, p2, d1, _ = base
    db.agendar(p1, d1, "2026-10-01 09:00", "Consulta")
    with pytest.raises(db.ErroDeNegocio, match="indisponível"):
        db.agendar(p2, d1, "2026-10-01 09:00", "Retorno")


# Regra 2: o mesmo paciente não pode estar com dois profissionais ao mesmo tempo
def test_bloqueia_paciente_em_dois_lugares(base):
    p1, _, d1, d2 = base
    db.agendar(p1, d1, "2026-10-01 09:00", "Consulta")
    with pytest.raises(db.ErroDeNegocio, match="outro atendimento"):
        db.agendar(p1, d2, "2026-10-01 09:00", "Consulta")


# ------------------------------------------------------------ cancelamento e reativação
# Cancelar libera o horário: outro paciente pode agendar no mesmo slot
def test_cancelado_libera_horario(base):
    p1, p2, d1, _ = base
    a = db.agendar(p1, d1, "2026-10-01 09:00", "Consulta")
    db.alterar_situacao(a, "cancelado")
    db.agendar(p2, d1, "2026-10-01 09:00", "Retorno")  # não deve falhar


# Se o horário de um cancelado foi ocupado por outro, não dá para reativá-lo
def test_reativar_cancelado_com_horario_ocupado_falha(base):
    p1, p2, d1, _ = base
    a = db.agendar(p1, d1, "2026-10-01 09:00", "Consulta")
    db.alterar_situacao(a, "cancelado")
    db.agendar(p2, d1, "2026-10-01 09:00", "Retorno")
    with pytest.raises(db.ErroDeNegocio):
        db.alterar_situacao(a, "agendado")


# ------------------------------------------------------------ reagendamento
# Reagendar para um horário livre atualiza data e hora do atendimento
def test_reagendar(base):
    p1, _, d1, _ = base
    a = db.agendar(p1, d1, "2026-10-01 09:00", "Consulta")
    db.reagendar(a, "2026-10-02 10:30")
    assert db.obter_atendimento(a)["data_hora"] == "2026-10-02 10:30"


# Reagendar para um horário já ocupado pelo mesmo profissional deve falhar
def test_reagendar_para_horario_ocupado_falha(base):
    p1, p2, d1, _ = base
    db.agendar(p1, d1, "2026-10-01 09:00", "Consulta")
    b = db.agendar(p2, d1, "2026-10-01 09:30", "Consulta")
    with pytest.raises(db.ErroDeNegocio):
        db.reagendar(b, "2026-10-01 09:00")


# Reagendar para o próprio horário não pode acusar conflito consigo mesmo
# (é para isso que serve o parâmetro ignorar_id em _checar_conflitos)
def test_reagendar_para_o_mesmo_horario_nao_conflita_consigo(base):
    p1, _, d1, _ = base
    a = db.agendar(p1, d1, "2026-10-01 09:00", "Consulta")
    db.reagendar(a, "2026-10-01 09:00")


# ------------------------------------------------------------ situação
# Uma situação que não está na lista SITUACOES deve ser recusada
def test_situacao_invalida(base):
    p1, _, d1, _ = base
    a = db.agendar(p1, d1, "2026-10-01 09:00", "Consulta")
    with pytest.raises(db.ErroDeNegocio):
        db.alterar_situacao(a, "qualquer")


# ------------------------------------------------------------ exclusões
# Paciente com atendimento no histórico não pode ser excluído
def test_nao_exclui_paciente_com_historico(base):
    p1, _, d1, _ = base
    db.agendar(p1, d1, "2026-10-01 09:00", "Consulta")
    with pytest.raises(db.ErroDeNegocio):
        db.excluir_paciente(p1)


# Paciente sem nenhum atendimento pode ser excluído, e some da listagem
def test_exclui_paciente_sem_historico(base):
    _, p2, _, _ = base
    db.excluir_paciente(p2)
    assert all(p["id"] != p2 for p in db.listar_pacientes())


# Excluir atendimento apaga o registro; obter_atendimento passa a devolver None
def test_excluir_atendimento(base):
    p1, _, d1, _ = base
    a = db.agendar(p1, d1, "2026-10-01 09:00", "Consulta")
    db.excluir_atendimento(a)
    assert db.obter_atendimento(a) is None


# ------------------------------------------------------------ horários livres
# Dos três horários candidatos, o das 09:00 está ocupado e deve ficar de fora
def test_horarios_livres(base):
    p1, _, d1, _ = base
    db.agendar(p1, d1, "2026-10-01 09:00", "Consulta")
    livres = db.horarios_livres("2026-10-01", d1, ["08:30", "09:00", "09:30"])
    assert livres == ["08:30", "09:30"]


# ------------------------------------------------------------ busca e segurança
# Confere a busca por nome e que um texto de ataque SQL é tratado como texto comum:
# não encontra ninguém e, ao final, a tabela continua existindo com os 2 pacientes
def test_busca_paciente_e_sql_injection(base):
    assert len(db.listar_pacientes("Ana")) == 1
    assert db.listar_pacientes("'; DROP TABLE pacientes;--") == []
    assert len(db.listar_pacientes()) == 2


# ------------------------------------------------------------ relatórios
# Marca um atendimento como falta e outro como realizado, e confere:
# 1) o resumo por situação (um de cada) e
# 2) que o relatório por profissional contabiliza 1 falta
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
