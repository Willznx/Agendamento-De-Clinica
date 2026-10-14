# Agenda de Atendimentos de uma Clínica Popular

Projeto 02 — Desenvolvimento Rápido de Aplicações (Python + Streamlit + SQLite).

## 1. Problema

Uma clínica pequena recebe pedidos de consulta por telefone e WhatsApp. Sem uma agenda
central, dois pacientes podem ser marcados com o mesmo profissional no mesmo horário e as
faltas não são acompanhadas.

**Usuários:** recepcionista (principal), profissionais de saúde e pacientes (beneficiados).

> Preencha aqui, depois da entrevista, o nome do(a) entrevistado(a), o cargo e 2–3 falas
> que justificam as decisões do projeto.

## 2. Requisitos

**Funcionais**
| # | Requisito | CRUD |
|---|-----------|------|
| RF1 | Cadastrar pacientes (nome, telefone) | Create |
| RF2 | Cadastrar profissionais (nome, especialidade) | Create |
| RF3 | Agendar atendimento escolhendo paciente, profissional, dia, horário e serviço | Create |
| RF4 | Consultar a agenda por dia e por profissional, vendo horários livres | Read |
| RF5 | Buscar paciente por nome ou telefone | Read |
| RF6 | Reagendar e alterar situação (agendado, realizado, cancelado, falta) | Update |
| RF7 | Editar dados de pacientes, profissionais e observações | Update |
| RF8 | Cancelar atendimento (libera o horário) | Update |
| RF9 | Excluir registro feito por engano, com confirmação | Delete |
| RF10 | Relatório de atendimentos, cancelamentos e faltas por período | Read |

**Regras de negócio**
- RN1: um profissional não pode ter dois atendimentos no mesmo horário.
- RN2: um paciente não pode ter dois atendimentos no mesmo horário.
- RN3: atendimento **cancelado** libera o horário; reativá-lo exige o horário ainda livre.
- RN4: paciente/profissional com histórico não pode ser excluído (preserva relatórios).
- RN5: excluir e cancelar exigem confirmação explícita.
- RN6: guardar só o necessário (nome e telefone); **sem dados clínicos sensíveis**
  (LGPD — dados de saúde são dados sensíveis).

**Não funcionais:** roda localmente com um único arquivo de banco; interface em português;
consultas parametrizadas (sem SQL injection).

## 3. Modelo de dados

```
pacientes (id, nome, telefone, criado_em)
profissionais (id, nome, especialidade)
atendimentos (id, paciente_id → pacientes, profissional_id → profissionais,
              data_hora 'AAAA-MM-DD HH:MM', servico, situacao, observacao)
```

- `situacao` ∈ {agendado, realizado, cancelado, falta} (restrição `CHECK`).
- Índice único parcial `(profissional_id, data_hora) WHERE situacao <> 'cancelado'`
  garante RN1 no próprio banco, mesmo se dois usuários agendarem ao mesmo tempo.

## 4. Como rodar

```bash
pip install -r requirements.txt
python seed.py            # opcional: dados de exemplo
streamlit run app.py
python -m pytest          # testes automatizados
```

## 5. Estrutura

| Arquivo | Papel |
|---------|-------|
| `db.py` | Banco, validações e regras de negócio (sem Streamlit) |
| `app.py` | Interface: 5 páginas |
| `test_db.py` | 18 testes das regras e do CRUD |
| `test_app.py` | Testes de fumaça: cada página abre sem erro |
| `seed.py` | Dados de exemplo |

## 6. Decisões da equipe

- **Regras separadas da interface** (`db.py`): permite testar sem abrir o navegador.
- **Cancelar ≠ excluir:** cancelar mantém o histórico para o relatório de faltas.
- **Só horários livres no formulário:** previne o erro em vez de só avisar depois.
- **Intervalos de 30 min, 08:00–17:30:** ajuste a lista `HORARIOS` em `app.py` após
  confirmar com a clínica.
- **Sem login:** fora do escopo de 8 semanas; melhoria futura.

## 7. Melhorias futuras
Login por perfil, lembrete por WhatsApp, agenda semanal, exportar CSV, horários de
funcionamento por profissional.
