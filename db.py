"""Camada de dados da Agenda de Atendimentos (SQLite).

Toda regra de negócio fica aqui, longe da interface, para poder ser testada.
Todas as consultas usam parâmetros (?) para evitar SQL injection.
"""
import os
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime

# Caminho do arquivo do banco. Pode ser trocado pela variável de ambiente CLINICA_DB
# (útil para usar um banco separado nos testes); por padrão cria "clinica.db" na pasta atual.
DB_PATH = os.environ.get("CLINICA_DB", "clinica.db")
# Situações possíveis de um atendimento (devem bater com o CHECK da tabela abaixo)
SITUACOES = ["agendado", "realizado", "cancelado", "falta"]
# Formato único de data/hora usado em todo o sistema, ex.: "2026-10-28 14:30"
FORMATO_DATA_HORA = "%Y-%m-%d %H:%M"

# Script de criação do banco, com três tabelas:
#   pacientes      -> quem é atendido (nome e telefone)
#   profissionais  -> quem atende (nome e especialidade)
#   atendimentos   -> liga paciente + profissional + data/hora + serviço + situação
# O "IF NOT EXISTS" permite rodar o script várias vezes sem apagar nem duplicar nada.
# O índice único no final impede dois atendimentos ativos do mesmo profissional
# no mesmo horário (cancelados ficam de fora, pois liberam o horário).
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
    # A interface (app.py) captura esta exceção e exibe a mensagem na tela.
    # Qualquer outro tipo de erro continua sendo tratado como falha inesperada.


# Gerenciador de contexto: usado com "with conexao() as con:", abre e fecha a conexão
# automaticamente em todas as funções abaixo.
@contextmanager
def conexao():
    con = sqlite3.connect(DB_PATH)
    # Permite acessar as colunas pelo nome (ex.: linha["nome"]) em vez de só por posição
    con.row_factory = sqlite3.Row
    # O SQLite não verifica chaves estrangeiras por padrão; aqui ativamos a verificação
    con.execute("PRAGMA foreign_keys = ON")
    try:
        yield con
        # Se o bloco "with" terminou sem erro, grava as alterações
        con.commit()
    except Exception:
        # Se algo falhou, desfaz tudo o que foi feito nessa conexão e repassa o erro
        con.rollback()
        raise
    finally:
        # Sempre fecha a conexão, dando certo ou não
        con.close()


def init_db():
    # Cria as tabelas e o índice, se ainda não existirem (chamada na inicialização do app)
    with conexao() as con:
        con.executescript(SCHEMA)


# ---------------------------------------------------------------- validações
# Funções internas (começam com "_") que limpam e validam os dados antes de salvar.
def _limpar_telefone(telefone: str) -> str:
    # Remove tudo que não for dígito: "(86) 99999-9999" vira "86999999999"
    digitos = re.sub(r"\D", "", telefone or "")
    # Aceita só DDD + número: 10 dígitos (fixo) ou 11 (celular)
    if len(digitos) not in (10, 11):
        raise ErroDeNegocio("Telefone inválido: informe DDD + número (10 ou 11 dígitos).")
    return digitos


def _validar_texto(valor: str, campo: str) -> str:
    # Tira espaços das pontas e exige pelo menos 2 caracteres (também trata None)
    valor = (valor or "").strip()
    if len(valor) < 2:
        raise ErroDeNegocio(f"{campo} é obrigatório (mínimo 2 caracteres).")
    return valor


def _validar_data_hora(data_hora: str) -> str:
    # Tenta converter o texto para data/hora; se não bater com o formato, é inválido
    try:
        datetime.strptime(data_hora, FORMATO_DATA_HORA)
    except (ValueError, TypeError):
        raise ErroDeNegocio("Data/hora inválida.")
    return data_hora


def _validar_situacao(situacao: str) -> str:
    # Garante que a situação seja uma das permitidas na lista SITUACOES
    if situacao not in SITUACOES:
        raise ErroDeNegocio(f"Situação inválida. Use: {', '.join(SITUACOES)}.")
    return situacao


# ----------------------------------------------------------------- pacientes
def criar_paciente(nome, telefone) -> int:
    # Valida e normaliza os dados antes de tocar no banco
    nome = _validar_texto(nome, "Nome")
    telefone = _limpar_telefone(telefone)
    with conexao() as con:
        # Os "?" são preenchidos pela tupla, o que evita SQL injection
        cur = con.execute(
            "INSERT INTO pacientes (nome, telefone) VALUES (?, ?)", (nome, telefone)
        )
        # Devolve o id do paciente recém-criado
        return cur.lastrowid


def listar_pacientes(busca: str = ""):
    # Busca parcial (LIKE) no nome OU no telefone; com busca vazia, lista todos.
    # Como o telefone é salvo só com dígitos, a busca por telefone deve usar só números.
    with conexao() as con:
        return con.execute(
            "SELECT * FROM pacientes WHERE nome LIKE ? OR telefone LIKE ? ORDER BY nome",
            (f"%{busca.strip()}%", f"%{busca.strip()}%"),
        ).fetchall()


def atualizar_paciente(paciente_id, nome, telefone):
    # Mesmas validações do cadastro, depois atualiza o registro pelo id
    nome = _validar_texto(nome, "Nome")
    telefone = _limpar_telefone(telefone)
    with conexao() as con:
        con.execute(
            "UPDATE pacientes SET nome = ?, telefone = ? WHERE id = ?",
            (nome, telefone, paciente_id),
        )


def excluir_paciente(paciente_id):
    with conexao() as con:
        # Conta quantos atendimentos o paciente tem no histórico
        n = con.execute(
            "SELECT COUNT(*) FROM atendimentos WHERE paciente_id = ?", (paciente_id,)
        ).fetchone()[0]
        # Se houver histórico, bloqueia a exclusão para não perder o registro dos atendimentos
        if n:
            raise ErroDeNegocio(
                f"Este paciente tem {n} atendimento(s) no histórico e não pode ser excluído. "
                "Cancele ou exclua os atendimentos antes."
            )
        con.execute("DELETE FROM pacientes WHERE id = ?", (paciente_id,))


# ------------------------------------------------------------- profissionais
def criar_profissional(nome, especialidade) -> int:
    # Valida os dois campos e insere; devolve o id criado
    nome = _validar_texto(nome, "Nome")
    especialidade = _validar_texto(especialidade, "Especialidade")
    with conexao() as con:
        cur = con.execute(
            "INSERT INTO profissionais (nome, especialidade) VALUES (?, ?)",
            (nome, especialidade),
        )
        return cur.lastrowid


def listar_profissionais():
    # Lista todos os profissionais em ordem alfabética
    with conexao() as con:
        return con.execute("SELECT * FROM profissionais ORDER BY nome").fetchall()


def atualizar_profissional(profissional_id, nome, especialidade):
    # Valida e atualiza nome e especialidade do profissional
    nome = _validar_texto(nome, "Nome")
    especialidade = _validar_texto(especialidade, "Especialidade")
    with conexao() as con:
        con.execute(
            "UPDATE profissionais SET nome = ?, especialidade = ? WHERE id = ?",
            (nome, especialidade, profissional_id),
        )


def excluir_profissional(profissional_id):
    with conexao() as con:
        # Mesma lógica da exclusão de paciente: não apaga quem tem atendimentos no histórico
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
    # Ao reagendar, o próprio atendimento não deve contar como conflito consigo mesmo.
    # Quando não há id para ignorar, usa -1, que nunca existe na tabela.
    ignorar = ignorar_id or -1
    # Regra 1: procura outro atendimento ativo do mesmo profissional nesse horário
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
    # Regra 2: procura outro atendimento ativo do mesmo paciente nesse horário (com qualquer profissional)
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
    # Valida data/hora e serviço antes de abrir o banco
    data_hora = _validar_data_hora(data_hora)
    servico = _validar_texto(servico, "Serviço")
    with conexao() as con:
        # Verificação amigável: gera uma mensagem clara dizendo quem está ocupando o horário
        _checar_conflitos(con, paciente_id, profissional_id, data_hora)
        try:
            cur = con.execute(
                """INSERT INTO atendimentos
                   (paciente_id, profissional_id, data_hora, servico, observacao)
                   VALUES (?, ?, ?, ?, ?)""",
                (paciente_id, profissional_id, data_hora, servico, observacao.strip()),
            )
        except sqlite3.IntegrityError:
            # Rede de segurança: se outra pessoa ocupou o horário entre a checagem e o INSERT,
            # o índice único do banco recusa e o erro é traduzido para mensagem amigável
            raise ErroDeNegocio("Horário indisponível (acabou de ser ocupado).")
        return cur.lastrowid


def listar_agenda(data: str, profissional_id=None):
    """Atendimentos de um dia (AAAA-MM-DD), opcionalmente de um profissional."""
    # Consulta base: junta atendimentos com paciente e profissional para trazer os nomes.
    # substr(data_hora, 1, 10) pega só a parte da data ("AAAA-MM-DD").
    sql = """SELECT a.*, p.nome AS paciente, p.telefone, pr.nome AS profissional
             FROM atendimentos a
             JOIN pacientes p ON p.id = a.paciente_id
             JOIN profissionais pr ON pr.id = a.profissional_id
             WHERE substr(a.data_hora, 1, 10) = ?"""
    params = [data]
    # Filtro opcional: só acrescenta a condição se um profissional foi informado
    if profissional_id:
        sql += " AND a.profissional_id = ?"
        params.append(profissional_id)
    # Ordena por horário e, em caso de empate, pelo nome do profissional
    sql += " ORDER BY a.data_hora, pr.nome"
    with conexao() as con:
        return con.execute(sql, params).fetchall()


def obter_atendimento(atendimento_id):
    # Busca um único atendimento pelo id (retorna None se não existir)
    with conexao() as con:
        return con.execute(
            "SELECT * FROM atendimentos WHERE id = ?", (atendimento_id,)
        ).fetchone()


def horarios_livres(data: str, profissional_id, horarios):
    # Conjunto de horários "HH:MM" já ocupados por atendimentos ativos nesse dia
    ocupados = {
        a["data_hora"][11:]
        for a in listar_agenda(data, profissional_id)
        if a["situacao"] != "cancelado"
    }
    # Devolve, da lista de horários possíveis, apenas os que não estão ocupados
    return [h for h in horarios if h not in ocupados]


def reagendar(atendimento_id, novo_data_hora, novo_profissional_id=None):
    novo_data_hora = _validar_data_hora(novo_data_hora)
    with conexao() as con:
        # Carrega o atendimento atual para saber paciente, profissional e situação
        atual = con.execute(
            "SELECT * FROM atendimentos WHERE id = ?", (atendimento_id,)
        ).fetchone()
        if not atual:
            raise ErroDeNegocio("Atendimento não encontrado.")
        # Se nenhum profissional novo foi informado, mantém o atual
        prof = novo_profissional_id or atual["profissional_id"]
        # Atendimento cancelado não ocupa horário, então só checa conflito nos demais
        if atual["situacao"] != "cancelado":
            _checar_conflitos(con, atual["paciente_id"], prof, novo_data_hora, atendimento_id)
        try:
            con.execute(
                "UPDATE atendimentos SET data_hora = ?, profissional_id = ? WHERE id = ?",
                (novo_data_hora, prof, atendimento_id),
            )
        except sqlite3.IntegrityError:
            # Rede de segurança: o índice único do banco recusou o horário
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
    # Atualiza apenas serviço e observação; o serviço é obrigatório, a observação pode ser vazia
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
    # Conta quantos atendimentos há em cada situação dentro do período (datas inclusivas)
    with conexao() as con:
        return con.execute(
            """SELECT situacao, COUNT(*) AS total FROM atendimentos
               WHERE substr(data_hora,1,10) BETWEEN ? AND ?
               GROUP BY situacao""",
            (data_ini, data_fim),
        ).fetchall()


def faltas_por_profissional(data_ini: str, data_fim: str):
    # Para cada profissional, no período: total de atendimentos, faltas e cancelamentos.
    # SUM(condição) funciona no SQLite porque a comparação vale 1 (verdadeiro) ou 0 (falso).
    # O resultado vem ordenado de quem tem mais faltas para quem tem menos.
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
