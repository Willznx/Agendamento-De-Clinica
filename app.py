"""Interface Streamlit da Agenda de Atendimentos.
Rodar com:  streamlit run app.py
"""
from datetime import date, datetime, time, timedelta

import pandas as pd
import streamlit as st

import db

st.set_page_config(page_title="Agenda da Clínica", page_icon="🩺", layout="wide")
db.init_db()

HORARIOS = [
    (datetime.combine(date.today(), time(8, 0)) + timedelta(minutes=30 * i)).strftime("%H:%M")
    for i in range(20)  # 08:00 até 17:30
]
ROTULO_SITUACAO = {
    "agendado": "🟦 Agendado",
    "realizado": "🟩 Realizado",
    "cancelado": "⬜ Cancelado",
    "falta": "🟥 Falta",
}


# ------------------------------------------------------------------ utilidades
def aviso(tipo, msg):
    """Guarda a mensagem para aparecer depois do st.rerun()."""
    st.session_state["aviso"] = (tipo, msg)


def mostrar_aviso():
    if "aviso" in st.session_state:
        tipo, msg = st.session_state.pop("aviso")
        getattr(st, tipo)(msg)


def formatar_telefone(t: str) -> str:
    if len(t) == 11:
        return f"({t[:2]}) {t[2:7]}-{t[7:]}"
    return f"({t[:2]}) {t[2:6]}-{t[6:]}"


def executar(acao, msg_ok, *args, **kwargs):
    """Chama uma função de db.py tratando erros de negócio de forma amigável."""
    try:
        resultado = acao(*args, **kwargs)
        aviso("success", msg_ok)
        st.rerun()
        return resultado
    except db.ErroDeNegocio as e:
        st.error(str(e))


def opcoes_pacientes():
    return {f"{p['nome']} — {formatar_telefone(p['telefone'])}": p["id"] for p in db.listar_pacientes()}


def opcoes_profissionais():
    return {f"{p['nome']} ({p['especialidade']})": p["id"] for p in db.listar_profissionais()}


# ---------------------------------------------------------------------- páginas
def pagina_agenda():
    st.header("📅 Agenda do dia")
    mostrar_aviso()
    profs = opcoes_profissionais()

    c1, c2 = st.columns([1, 2])
    dia = c1.date_input("Dia", value=date.today(), format="DD/MM/YYYY")
    escolha = c2.selectbox("Profissional", ["Todos"] + list(profs))
    prof_id = None if escolha == "Todos" else profs[escolha]
    dia_txt = dia.isoformat()

    agenda = db.listar_agenda(dia_txt, prof_id)
    ativos = [a for a in agenda if a["situacao"] != "cancelado"]
    m1, m2, m3 = st.columns(3)
    m1.metric("Atendimentos no dia", len(ativos))
    m2.metric("Já realizados", sum(a["situacao"] == "realizado" for a in agenda))
    m3.metric("Faltas", sum(a["situacao"] == "falta" for a in agenda))

    if agenda:
        df = pd.DataFrame(
            {
                "Hora": [a["data_hora"][11:] for a in agenda],
                "Paciente": [a["paciente"] for a in agenda],
                "Telefone": [formatar_telefone(a["telefone"]) for a in agenda],
                "Profissional": [a["profissional"] for a in agenda],
                "Serviço": [a["servico"] for a in agenda],
                "Situação": [ROTULO_SITUACAO[a["situacao"]] for a in agenda],
            }
        )
        st.dataframe(df, width="stretch", hide_index=True)
    else:
        st.info("Nenhum atendimento neste dia.")

    if prof_id:
        livres = db.horarios_livres(dia_txt, prof_id, HORARIOS)
        st.caption("Horários livres: " + (", ".join(livres) if livres else "nenhum"))

    if agenda:
        st.divider()
        st.subheader("Alterar atendimento")
        rotulos = {
            f"{a['data_hora'][11:]} — {a['paciente']} ({a['profissional']})": a["id"]
            for a in agenda
        }
        sel = st.selectbox("Selecione o atendimento", list(rotulos))
        editar_atendimento(rotulos[sel], profs)


def editar_atendimento(aid, profs):
    a = db.obter_atendimento(aid)
    tab1, tab2, tab3, tab4 = st.tabs(["Situação", "Reagendar", "Serviço e observação", "Excluir"])

    with tab1:
        idx = db.SITUACOES.index(a["situacao"])
        nova = st.radio(
            "Situação", db.SITUACOES, index=idx, horizontal=True,
            format_func=lambda s: ROTULO_SITUACAO[s], key=f"sit_{aid}",
        )
        if nova == "cancelado" and a["situacao"] != "cancelado":
            st.warning("O horário será liberado para outro paciente.")
            ok = st.checkbox("Confirmo o cancelamento", key=f"confcanc_{aid}")
        else:
            ok = True
        if st.button("Salvar situação", disabled=(nova == a["situacao"] or not ok), key=f"bs_{aid}"):
            executar(db.alterar_situacao, "Situação atualizada.", aid, nova)

    with tab2:
        d_atual = datetime.strptime(a["data_hora"], db.FORMATO_DATA_HORA)
        with st.form(f"reag_{aid}"):
            nome_prof = next(k for k, v in profs.items() if v == a["profissional_id"])
            p = st.selectbox("Profissional", list(profs), index=list(profs).index(nome_prof))
            nd = st.date_input("Novo dia", value=d_atual.date(), format="DD/MM/YYYY")
            h_atual = d_atual.strftime("%H:%M")
            nh = st.selectbox(
                "Novo horário", HORARIOS,
                index=HORARIOS.index(h_atual) if h_atual in HORARIOS else 0,
            )
            if st.form_submit_button("Reagendar"):
                executar(db.reagendar, "Atendimento reagendado.", aid, f"{nd.isoformat()} {nh}", profs[p])

    with tab3:
        with st.form(f"obs_{aid}"):
            serv = st.text_input("Serviço", value=a["servico"])
            obs = st.text_area(
                "Observação (não registre dados clínicos sensíveis)", value=a["observacao"] or ""
            )
            if st.form_submit_button("Salvar"):
                executar(db.atualizar_observacao, "Dados atualizados.", aid, serv, obs)

    with tab4:
        st.warning(
            "Excluir apaga o registro para sempre. Para desmarcar um atendimento real, "
            "use **Situação → Cancelado**."
        )
        ok = st.checkbox("Entendo que a exclusão é definitiva", key=f"confdel_{aid}")
        if st.button("Excluir registro", type="primary", disabled=not ok, key=f"bd_{aid}"):
            executar(db.excluir_atendimento, "Registro excluído.", aid)


def pagina_novo_agendamento():
    st.header("➕ Novo agendamento")
    mostrar_aviso()
    pacientes, profs = opcoes_pacientes(), opcoes_profissionais()
    if not pacientes or not profs:
        st.info("Cadastre ao menos um paciente e um profissional antes de agendar.")
        return

    c1, c2 = st.columns(2)
    pac = c1.selectbox("Paciente", list(pacientes))
    prof = c2.selectbox("Profissional", list(profs))
    c3, c4 = st.columns(2)
    dia = c3.date_input("Dia", value=date.today(), min_value=date.today(), format="DD/MM/YYYY")
    livres = db.horarios_livres(dia.isoformat(), profs[prof], HORARIOS)
    if not livres:
        c4.warning("Sem horários livres neste dia para este profissional.")
    hora = c4.selectbox("Horário (só aparecem os livres)", livres)
    servico = st.text_input("Serviço", placeholder="Ex.: Consulta, Retorno, Vacina")
    obs = st.text_area("Observação (opcional; sem dados clínicos sensíveis)")

    if st.button("Agendar", type="primary", disabled=not livres):
        if hora and datetime.strptime(f"{dia} {hora}", db.FORMATO_DATA_HORA) < datetime.now():
            st.error("Esse horário já passou.")
        else:
            executar(
                db.agendar, "Atendimento agendado!",
                pacientes[pac], profs[prof], f"{dia.isoformat()} {hora}", servico, obs,
            )


def pagina_pacientes():
    st.header("👤 Pacientes")
    mostrar_aviso()
    with st.expander("Cadastrar novo paciente", expanded=False):
        with st.form("novo_pac", clear_on_submit=True):
            nome = st.text_input("Nome completo")
            tel = st.text_input("Telefone / WhatsApp", placeholder="(86) 99999-9999")
            if st.form_submit_button("Cadastrar"):
                executar(db.criar_paciente, "Paciente cadastrado.", nome, tel)

    busca = st.text_input("🔎 Buscar por nome ou telefone")
    lista = db.listar_pacientes(busca)
    if not lista:
        st.info("Nenhum paciente encontrado.")
        return
    st.dataframe(
        pd.DataFrame({"Nome": [p["nome"] for p in lista],
                      "Telefone": [formatar_telefone(p["telefone"]) for p in lista]}),
        width="stretch", hide_index=True,
    )
    st.subheader("Editar ou excluir")
    rot = {f"{p['nome']} — {formatar_telefone(p['telefone'])}": p for p in lista}
    p = rot[st.selectbox("Paciente", list(rot))]
    with st.form(f"edit_pac_{p['id']}"):
        n = st.text_input("Nome", value=p["nome"])
        t = st.text_input("Telefone", value=formatar_telefone(p["telefone"]))
        if st.form_submit_button("Salvar alterações"):
            executar(db.atualizar_paciente, "Paciente atualizado.", p["id"], n, t)
    ok = st.checkbox("Confirmo a exclusão deste paciente", key=f"cdp_{p['id']}")
    if st.button("Excluir paciente", disabled=not ok, key=f"bdp_{p['id']}"):
        executar(db.excluir_paciente, "Paciente excluído.", p["id"])


def pagina_profissionais():
    st.header("🩺 Profissionais")
    mostrar_aviso()
    with st.expander("Cadastrar novo profissional"):
        with st.form("novo_prof", clear_on_submit=True):
            nome = st.text_input("Nome")
            esp = st.text_input("Especialidade", placeholder="Ex.: Clínica geral")
            if st.form_submit_button("Cadastrar"):
                executar(db.criar_profissional, "Profissional cadastrado.", nome, esp)

    lista = db.listar_profissionais()
    if not lista:
        st.info("Nenhum profissional cadastrado.")
        return
    st.dataframe(
        pd.DataFrame({"Nome": [p["nome"] for p in lista],
                      "Especialidade": [p["especialidade"] for p in lista]}),
        width="stretch", hide_index=True,
    )
    rot = {f"{p['nome']} ({p['especialidade']})": p for p in lista}
    p = rot[st.selectbox("Editar ou excluir", list(rot))]
    with st.form(f"edit_prof_{p['id']}"):
        n = st.text_input("Nome", value=p["nome"])
        e = st.text_input("Especialidade", value=p["especialidade"])
        if st.form_submit_button("Salvar alterações"):
            executar(db.atualizar_profissional, "Profissional atualizado.", p["id"], n, e)
    ok = st.checkbox("Confirmo a exclusão deste profissional", key=f"cdpr_{p['id']}")
    if st.button("Excluir profissional", disabled=not ok, key=f"bdpr_{p['id']}"):
        executar(db.excluir_profissional, "Profissional excluído.", p["id"])


def pagina_relatorios():
    st.header("📊 Relatórios")
    hoje = date.today()
    c1, c2 = st.columns(2)
    ini = c1.date_input("De", value=hoje - timedelta(days=30), format="DD/MM/YYYY")
    fim = c2.date_input("Até", value=hoje, format="DD/MM/YYYY")
    if ini > fim:
        st.error("A data inicial não pode ser maior que a final.")
        return

    resumo = db.resumo_por_situacao(ini.isoformat(), fim.isoformat())
    if not resumo:
        st.info("Sem atendimentos no período.")
        return
    total = sum(r["total"] for r in resumo)
    contagem = {r["situacao"]: r["total"] for r in resumo}
    base = contagem.get("realizado", 0) + contagem.get("falta", 0)
    m1, m2, m3 = st.columns(3)
    m1.metric("Total no período", total)
    m2.metric("Cancelados", contagem.get("cancelado", 0))
    m3.metric("Taxa de faltas", f"{contagem.get('falta', 0) / base:.0%}" if base else "—",
              help="Faltas ÷ (realizados + faltas)")

    st.bar_chart(pd.Series(contagem, name="Atendimentos"))
    por_prof = db.faltas_por_profissional(ini.isoformat(), fim.isoformat())
    st.subheader("Por profissional")
    st.dataframe(
        pd.DataFrame([dict(r) for r in por_prof]).rename(
            columns={"profissional": "Profissional", "total": "Total",
                     "faltas": "Faltas", "cancelados": "Cancelados"}),
        width="stretch", hide_index=True,
    )


# ------------------------------------------------------------------- navegação
PAGINAS = {
    "📅 Agenda do dia": pagina_agenda,
    "➕ Novo agendamento": pagina_novo_agendamento,
    "👤 Pacientes": pagina_pacientes,
    "🩺 Profissionais": pagina_profissionais,
    "📊 Relatórios": pagina_relatorios,
}
with st.sidebar:
    st.title("Agenda da Clínica")
    escolha = st.radio("Menu", list(PAGINAS), label_visibility="collapsed")
    st.caption("Guarde apenas o necessário: nome e telefone. Sem dados clínicos sensíveis.")
PAGINAS[escolha]()
