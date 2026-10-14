# Roteiros: entrevista, testes com usuários e apresentação

## A. Entrevista (semanas 1–2) — recepcionista ou profissional de uma clínica
1. Como os pacientes pedem consulta hoje? (telefone, WhatsApp, presencial)
2. Onde vocês anotam a agenda? O que acontece quando dois pacientes são marcados no mesmo horário?
3. Quantos atendimentos por dia? Quantos profissionais?
4. Qual a duração média de uma consulta? Existem tipos de serviço diferentes?
5. Como lidam com faltas e cancelamentos? Alguém acompanha quantas são?
6. Que informações do paciente vocês realmente precisam na hora de agendar?
7. Quem usaria o sistema? Tem computador ou só celular?
8. O que faria você **parar** de usar um sistema novo?
Peça para ver (ou fotografar, sem dados pessoais) a agenda atual.

## B. Teste com usuário (semanas 7–8) — peça para fazer, sem ajudar
| # | Tarefa | Sucesso? | Tempo | Dificuldade observada |
|---|--------|----------|-------|-----------------------|
| 1 | Cadastrar um paciente novo | | | |
| 2 | Agendar consulta para amanhã às 09:00 | | | |
| 3 | Tentar agendar o mesmo horário para outro paciente (deve ser bloqueado) | | | |
| 4 | Reagendar o atendimento para outro dia | | | |
| 5 | Registrar que o paciente faltou | | | |
| 6 | Cancelar um atendimento | | | |
| 7 | Ver a agenda de hoje de um profissional | | | |
| 8 | Ver quantas faltas houve no mês | | | |
Depois: "O que foi confuso?" "O que faltou?" Registre as melhorias feitas a partir disso.

## C. Apresentação (8–10 min)
1. **(1 min)** O problema e o usuário real; uma fala da entrevista.
2. **(1 min)** O modelo de dados e por que o índice único protege contra horário duplo.
3. **(4 min)** Demo ao vivo: cadastrar → agendar → tentar duplicar (erro amigável) →
   reagendar → marcar falta → relatório.
4. **(1 min)** Testes: `pytest` (23 testes) + resultados do teste com usuário.
5. **(1 min)** O que mudou depois do feedback e melhorias futuras.
Dica: rode `python seed.py` antes para a agenda não estar vazia.
