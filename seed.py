"""Popula o banco com dados de exemplo para a demonstração.  python seed.py"""
from datetime import date, timedelta
import db

# Cria o arquivo do banco e as tabelas, caso ainda não existam
db.init_db()
# Proteção: se já houver pacientes cadastrados, o script para aqui (SystemExit encerra
# o programa com a mensagem) para não duplicar nem misturar os dados de exemplo
if db.listar_pacientes():
    raise SystemExit("O banco já tem dados; apague clinica.db para recriar.")

# --- Cadastros básicos ---
# Cada função "criar_*" devolve o id do registro, guardado em variáveis
# para ser usado depois ao montar os agendamentos.
# O telefone pode ter máscara; o db.py remove tudo que não for dígito antes de salvar.
ana = db.criar_paciente("Ana Souza", "(86) 99999-1111")
joao = db.criar_paciente("João Lima", "(86) 98888-2222")
maria = db.criar_paciente("Maria Oliveira", "(86) 97777-3333")
marta = db.criar_profissional("Dra. Marta Reis", "Clínica geral")
paulo = db.criar_profissional("Dr. Paulo Nunes", "Pediatria")

# --- Agendamentos ---
# As datas são calculadas a partir de hoje, para a demonstração sempre mostrar
# atendimentos no dia atual e no dia seguinte, não importa quando for executada
hoje = date.today()
amanha = hoje + timedelta(days=1)
# Formato esperado pelo banco: "AAAA-MM-DD HH:MM" (o f-string converte a data para esse texto)
# Hoje: Ana às 08:00 e João às 09:00, ambos com a Dra. Marta
db.agendar(ana, marta, f"{hoje} 08:00", "Consulta")
db.agendar(joao, marta, f"{hoje} 09:00", "Retorno")
# Amanhã: Maria com o Dr. Paulo, às 10:30
db.agendar(maria, paulo, f"{amanha} 10:30", "Consulta")
# Marca o primeiro atendimento de hoje (o das 08:00, pois a lista vem ordenada por horário)
# como "realizado", para a demonstração mostrar também esse status
db.alterar_situacao(db.listar_agenda(str(hoje))[0]["id"], "realizado")
print("Dados de exemplo criados.")
