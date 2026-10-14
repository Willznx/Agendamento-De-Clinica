"""Camada de dados da Agenda de Atendimentos (SQLite).

Toda regra de negócio fica aqui, longe da interface, para poder ser testada.
Todas as consultas usam parâmetros (?) para evitar SQL injection.
"""
import os
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime

DB_PATH = os.environ.get("CLINICA_DB", "clinica.db")
SITUACOES = ["agendado", "realizado", "cancelado", "falta"]
FORMATO_DATA_HORA = "%Y-%m-%d %H:%M"

SCHEMA = """
CREATE TABLE IF NOT EXISTS pacientes (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    nome      TEXT NOT NULL,
    telefone  TEXT NOT NULL,
    criado_em TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS profissionais (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nome          TEXT NOT NULL,
    especialidade TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS atendimentos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id     INTEGER NOT NULL REFERENCES pacientes(id),
    profissional_id INTEGER NOT NULL REFERENCES profissionais(id),
    data_hora       TEXT NOT NULL,              -- 'AAAA-MM-DD HH:MM'
    servico         TEXT NOT NULL,
    situacao        TEXT NOT NULL DEFAULT 'agendado'
                    CHECK (situacao IN ('agendado','realizado','cancelado','falta')),
    observacao      TEXT DEFAULT ''             -- sem dados clínicos sensíveis
);

-- Última barreira contra horário duplo: mesmo profissional, mesmo horário,
-- exceto atendimentos cancelados (que liberam o horário).
CREATE UNIQUE INDEX IF NOT EXISTS ux_profissional_horario
    ON atendimentos(profissional_id, data_hora)
    WHERE situacao <> 'cancelado';
"""


class ErroDeNegocio(Exception):
    """Erro com mensagem amigável para mostrar ao usuário."""


@contextmanager
def conexao():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def init_db():
    with conexao() as con:
        con.executescript(SCHEMA)


# ---------------------------------------------------------------- validações
def _limpar_telefone(telefone: str) -> str:
    digitos = re.sub(r"\D", "", telefone or "")
    if len(digitos) not in (10, 11):
        raise ErroDeNegocio("Telefone inválido: informe DDD + número (10 ou 11 dígitos).")
    return digitos


def _validar_texto(valor: str, campo: str) -> str:
    valor = (valor or "").strip()
    if len(valor) < 2:
        raise ErroDeNegocio(f"{campo} é obrigatório (mínimo 2 caracteres).")
    return valor


def _validar_data_hora(data_hora: str) -> str:
    try:
        datetime.strptime(data_hora, FORMATO_DATA_HORA)
    except (ValueError, TypeError):
        raise ErroDeNegocio("Data/hora inválida.")
    return data_hora


def _validar_situacao(situacao: str) -> str:
    if situacao not in SITUACOES:
        raise ErroDeNegocio(f"Situação inválida. Use: {', '.join(SITUACOES)}.")
    return situacao


# ----------------------------------------------------------------- pacientes
def criar_paciente(nome, telefone) -> int:
    nome = _validar_texto(nome, "Nome")
    telefone = _limpar_telefone(telefone)
    with conexao() as con:
        cur = con.execute(
            "INSERT INTO pacientes (nome, telefone) VALUES (?, ?)", (nome, telefone)
        )
        return cur.lastrowid


def listar_pacientes(busca: str = ""):
    with conexao() as con:
        return con.execute(
            "SELECT * FROM pacientes WHERE nome LIKE ? OR telefone LIKE ? ORDER BY nome",
            (f"%{busca.strip()}%", f"%{busca.strip()}%"),
        ).fetchall()


def atualizar_paciente(paciente_id, nome, telefone):
    nome = _validar_texto(nome, "Nome")
    telefone = _limpar_telefone(telefone)
    with conexao() as con:
        con.execute(
            "UPDATE pacientes SET nome = ?, telefone = ? WHERE id = ?",
            (nome, telefone, paciente_id),
        )


def excluir_paciente(paciente_id):
    with conexao() as con:
        n = con.execute(
            "SELECT COUNT(*) FROM atendimentos WHERE paciente_id = ?", (paciente_id,)
        ).fetchone()[0]
        if n:
            raise ErroDeNegocio(
                f"Este paciente tem {n} atendimento(s) no histórico e não pode ser excluído. "
                "Cancele ou exclua os atendimentos antes."
            )
        con.execute("DELETE FROM pacientes WHERE id = ?", (paciente_id,))


# ------------------------------------------------------------- profissionais
def criar_profissional(nome, especialidade) -> int:
    nome = _validar_texto(nome, "Nome")
    especialidade = _validar_texto(especialidade, "Especialidade")
    with conexao() as con:
        cur = con.execute(
            "INSERT INTO profissionais (nome, especialidade) VALUES (?, ?)",
            (nome, especialidade),
        )
        return cur.lastrowid


def listar_profissionais():
    with conexao() as con:
        return con.execute("SELECT * FROM profissionais ORDER BY nome").fetchall()


def atualizar_profissional(profissional_id, nome, especialidade):
    nome = _validar_texto(nome, "Nome")
    especialidade = _validar_texto(especialidade, "Especialidade")
    with conexao() as con:
        con.execute(
            "UPDATE profissionais SET nome = ?, especialidade = ? WHERE id = ?",
            (nome, especialidade, profissional_id),
        )


def excluir_profissional(profissional_id):
    with conexao() as con:
        n = con.execute(
            "SELECT COUNT(*) FROM atendimentos WHERE profissional_id = ?",
            (profissional_id,),
        ).fetchone()[0]
        if n:
            raise ErroDeNegocio(
                f"Este profissional tem {n} atendimento(s) no histórico e não pode ser excluído."
            )
        con.execute("DELETE FROM profissionais WHERE id = ?", (profissional_id,))


# -------------------------------------------------------------- atendimentos
def _checar_conflitos(con, paciente_id, profissional_id, data_hora, ignorar_id=None):
    """Regra 1: profissional não pode ter 2 atendimentos no mesmo horário.
    Regra 2: paciente não pode estar em 2 atendimentos no mesmo horário."""
    ignorar = ignorar_id or -1
    ocupado = con.execute(
        """SELECT p.nome FROM atendimentos a
           JOIN pacientes p ON p.id = a.paciente_id
           WHERE a.profissional_id = ? AND a.data_hora = ?
             AND a.situacao <> 'cancelado' AND a.id <> ?""",
        (profissional_id, data_hora, ignorar),
    ).fetchone()
    if ocupado:
        raise ErroDeNegocio(
            f"Horário indisponível: o profissional já atende {ocupado['nome']} às "
            f"{data_hora[11:]} desse dia."
        )
    duplo = con.execute(
        """SELECT pr.nome FROM atendimentos a
           JOIN profissionais pr ON pr.id = a.profissional_id
           WHERE a.paciente_id = ? AND a.data_hora = ?
             AND a.situacao <> 'cancelado' AND a.id <> ?""",
        (paciente_id, data_hora, ignorar),
    ).fetchone()
    if duplo:
        raise ErroDeNegocio(
            f"Este paciente já tem outro atendimento nesse horário (com {duplo['nome']})."
        )


def agendar(paciente_id, profissional_id, data_hora, servico, observacao="") -> int:
    data_hora = _validar_data_hora(data_hora)
    servico = _validar_texto(servico, "Serviço")
    with conexao() as con:
        _checar_conflitos(con, paciente_id, profissional_id, data_hora)
        try:
            cur = con.execute(
                """INSERT INTO atendimentos
                   (paciente_id, profissional_id, data_hora, servico, observacao)
                   VALUES (?, ?, ?, ?, ?)""",
                (paciente_id, profissional_id, data_hora, servico, observacao.strip()),
            )
        except sqlite3.IntegrityError:
            raise ErroDeNegocio("Horário indisponível (acabou de ser ocupado).")
        return cur.lastrowid


def listar_agenda(data: str, profissional_id=None):
    """Atendimentos de um dia (AAAA-MM-DD), opcionalmente de um profissional."""
    sql = """SELECT a.*, p.nome AS paciente, p.telefone, pr.nome AS profissional
             FROM atendimentos a
             JOIN pacientes p ON p.id = a.paciente_id
             JOIN profissionais pr ON pr.id = a.profissional_id
             WHERE substr(a.data_hora, 1, 10) = ?"""
    params = [data]
    if profissional_id:
        sql += " AND a.profissional_id = ?"
        params.append(profissional_id)
    sql += " ORDER BY a.data_hora, pr.nome"
    with conexao() as con:
        return con.execute(sql, params).fetchall()


def obter_atendimento(atendimento_id):
    with conexao() as con:
        return con.execute(
            "SELECT * FROM atendimentos WHERE id = ?", (atendimento_id,)
        ).fetchone()


def horarios_livres(data: str, profissional_id, horarios):
    ocupados = {
        a["data_hora"][11:]
        for a in listar_agenda(data, profissional_id)
        if a["situacao"] != "cancelado"
    }
    return [h for h in horarios if h not in ocupados]


def reagendar(atendimento_id, novo_data_hora, novo_profissional_id=None):
    novo_data_hora = _validar_data_hora(novo_data_hora)
    with conexao() as con:
        atual = con.execute(
            "SELECT * FROM atendimentos WHERE id = ?", (atendimento_id,)
        ).fetchone()
        if not atual:
            raise ErroDeNegocio("Atendimento não encontrado.")
        prof = novo_profissional_id or atual["profissional_id"]
        if atual["situacao"] != "cancelado":
            _checar_conflitos(con, atual["paciente_id"], prof, novo_data_hora, atendimento_id)
        try:
            con.execute(
                "UPDATE atendimentos SET data_hora = ?, profissional_id = ? WHERE id = ?",
                (novo_data_hora, prof, atendimento_id),
            )
        except sqlite3.IntegrityError:
            raise ErroDeNegocio("Horário indisponível.")


def alterar_situacao(atendimento_id, situacao):
    situacao = _validar_situacao(situacao)
    with conexao() as con:
        atual = con.execute(
            "SELECT * FROM atendimentos WHERE id = ?", (atendimento_id,)
        ).fetchone()
        if not atual:
            raise ErroDeNegocio("Atendimento não encontrado.")
        # Reativar um cancelado exige que o horário ainda esteja livre.
        if atual["situacao"] == "cancelado" and situacao != "cancelado":
            _checar_conflitos(
                con, atual["paciente_id"], atual["profissional_id"],
                atual["data_hora"], atendimento_id,
            )
        con.execute(
            "UPDATE atendimentos SET situacao = ? WHERE id = ?", (situacao, atendimento_id)
        )


def atualizar_observacao(atendimento_id, servico, observacao):
    servico = _validar_texto(servico, "Serviço")
    with conexao() as con:
        con.execute(
            "UPDATE atendimentos SET servico = ?, observacao = ? WHERE id = ?",
            (servico, (observacao or "").strip(), atendimento_id),
        )


def excluir_atendimento(atendimento_id):
    """Remove definitivamente (uso: registro criado por engano).
    Para desmarcar um atendimento real, prefira alterar_situacao('cancelado')."""
    with conexao() as con:
        con.execute("DELETE FROM atendimentos WHERE id = ?", (atendimento_id,))


# ----------------------------------------------------------------- relatórios
def resumo_por_situacao(data_ini: str, data_fim: str):
    with conexao() as con:
        return con.execute(
            """SELECT situacao, COUNT(*) AS total FROM atendimentos
               WHERE substr(data_hora,1,10) BETWEEN ? AND ?
               GROUP BY situacao""",
            (data_ini, data_fim),
        ).fetchall()


def faltas_por_profissional(data_ini: str, data_fim: str):
    with conexao() as con:
        return con.execute(
            """SELECT pr.nome AS profissional,
                      COUNT(*) AS total,
                      SUM(a.situacao = 'falta') AS faltas,
                      SUM(a.situacao = 'cancelado') AS cancelados
               FROM atendimentos a JOIN profissionais pr ON pr.id = a.profissional_id
               WHERE substr(a.data_hora,1,10) BETWEEN ? AND ?
               GROUP BY pr.id ORDER BY faltas DESC""",
            (data_ini, data_fim),
        ).fetchall()
