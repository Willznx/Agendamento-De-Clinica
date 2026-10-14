"""Popula o banco com dados de exemplo para a demonstração.  python seed.py"""
from datetime import date, timedelta
import db

db.init_db()
if db.listar_pacientes():
    raise SystemExit("O banco já tem dados; apague clinica.db para recriar.")

ana = db.criar_paciente("Ana Souza", "(86) 99999-1111")
joao = db.criar_paciente("João Lima", "(86) 98888-2222")
maria = db.criar_paciente("Maria Oliveira", "(86) 97777-3333")
marta = db.criar_profissional("Dra. Marta Reis", "Clínica geral")
paulo = db.criar_profissional("Dr. Paulo Nunes", "Pediatria")

hoje = date.today()
amanha = hoje + timedelta(days=1)
db.agendar(ana, marta, f"{hoje} 08:00", "Consulta")
db.agendar(joao, marta, f"{hoje} 09:00", "Retorno")
db.agendar(maria, paulo, f"{amanha} 10:30", "Consulta")
db.alterar_situacao(db.listar_agenda(str(hoje))[0]["id"], "realizado")
print("Dados de exemplo criados.")
