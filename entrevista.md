
 ### Entrevista — Sistema de Agenda para Clínica

 **Personagens:**

 - **Gerente:** responsável pela clínica.
- **Antenor Santos, Helder Brandão e Willians Júnior:** responsáveis por entenderem o problema e propor uma solução.

---

 **Antenor:** Bom dia. Gostaria primeiro de entender como funciona o processo de agendamento atualmente. Como os pacientes marcam uma consulta?

 **Gerente:** Bom dia. Atualmente eles entram em contato principalmente pelo WhatsApp ou telefone. A recepcionista verifica se o profissional está disponível e marca o horário.

 **Willians Júnior:** E onde esse horário é registrado?

 **Gerente:** Esse é um dos nossos problemas. Às vezes a recepcionista anota em uma agenda de papel, às vezes em uma planilha e, em alguns casos, fica registrado apenas na conversa do WhatsApp.

 **Helder:** Então não existe um único lugar onde todos conseguem consultar os agendamentos?

 **Gerente:** Exatamente.

 **Antenor Santos:** Isso já causou algum problema?

 **Gerente:** Sim. Já aconteceu de duas pessoas serem marcadas para o mesmo horário. Também acontece de um profissional não saber que houve uma alteração no horário de um paciente.

 **Willians Júnior:** Entendi. E como vocês controlam os pacientes que faltam?

 **Gerente:** Atualmente não controlamos direito. A recepcionista pode perceber que o paciente não apareceu, mas isso não fica registrado de maneira organizada.

 **Helder:** Então seria importante registrar o status de cada consulta, por exemplo: agendada, confirmada, atendida, cancelada ou faltou?

 **Gerente:** Sim. Isso ajudaria bastante.

 **Antenor** Quem precisaria utilizar o sistema?

 **Gerente:** A recepcionista, os profissionais de saúde e os pacientes.

 **Willians Júnior:** Todos teriam o mesmo acesso?

 **Gerente:** Não. A recepcionista precisa controlar os agendamentos. Os profissionais precisam consultar sua própria agenda. Já os pacientes precisam conseguir marcar e acompanhar suas consultas.

 **Helder:** Entendi. Sobre os profissionais, um paciente pode escolher qual profissional deseja consultar?

 **Gerente:** Sim. Temos profissionais diferentes e cada um possui seus próprios horários.

 **Antenor:** E os profissionais possuem horários fixos?

 **Gerente:** Na maioria dos casos sim, mas eventualmente eles podem alterar a disponibilidade.

 **Willians:** Nesse caso, o sistema deveria permitir que a recepcionista ou o profissional bloqueasse determinados horários?

 **Gerente:** Sim. Por exemplo, se o profissional tiver uma reunião ou precisar sair, aquele horário não pode ficar disponível para pacientes.

 **Helder:** Perfeito. E quanto à duração das consultas? Todas têm o mesmo tempo?

 **Gerente:** Não necessariamente. Alguns atendimentos duram 30 minutos e outros podem durar uma hora.

 **Antenor:** Então o sistema precisa considerar a duração do atendimento antes de disponibilizar o próximo horário.

 **Gerente:** Exatamente.

 **Willians:** Vou fazer uma pergunta importante: quando alguém tentar marcar uma consulta, o sistema deve verificar automaticamente se aquele horário já está ocupado?

 **Gerente:** Sim. Esse é justamente um dos principais problemas que queremos resolver.

 **Helder:** Então, se alguém tentar agendar às 14h e já existir uma consulta nesse horário, o sistema deve impedir o agendamento.

 **Gerente:** Isso. E seria bom mostrar os horários disponíveis para evitar esse problema.

 **Antenor:** Certo. Sobre os pacientes, quais informações precisamos guardar?

 **Gerente:** Nome, telefone, talvez CPF, data de nascimento e histórico das consultas.

 **Willians:** E precisamos guardar informações médicas também?

 **Gerente:** Não nesse primeiro momento. Queremos apenas resolver a questão dos agendamentos.

 **Helder:** Ótimo. Então podemos manter o primeiro sistema focado na agenda e não tentar resolver tudo de uma vez.

 **Gerente:** Concordo.

 **Antenor:** Outra questão: o paciente agenda diretamente pelo sistema ou ainda poderá ligar e mandar mensagem pelo WhatsApp?

 **Gerente:** Ele poderá continuar usando telefone e WhatsApp. A recepcionista faria o cadastro no sistema nesses casos. Mas gostaríamos que, futuramente, o paciente também pudesse fazer o agendamento sozinho.

 **Willians:** Entendi. Então inicialmente podemos centralizar todos os agendamentos no sistema, independentemente de onde o pedido veio.

 **Gerente:** Exatamente.

 **Helder:** E vocês gostariam de algum tipo de lembrete para diminuir as faltas?

 **Gerente:** Sim. Seria muito interessante enviar uma mensagem lembrando o paciente da consulta.

 **Antenor:** Podemos considerar isso como uma funcionalidade do sistema. O paciente receberia um lembrete antes da consulta e poderia confirmar ou solicitar o cancelamento.

 **Gerente:** Gostei dessa ideia.

 **Willians:** E quando o paciente cancelar?

 **Gerente:** O horário deveria ficar disponível novamente para outra pessoa.

 **Helder:** Perfeito. E se ele simplesmente não aparecer?

 **Gerente:** A recepcionista ou o profissional deveria poder marcar como "faltou".

 **Antenor:** Assim podemos manter um histórico de faltas por paciente.

 **Gerente:** Sim.

 **Willians:** Acho que já tenho uma visão clara do problema. Vou resumir para confirmar se entendi corretamente.

 > Atualmente a clínica possui agendamentos espalhados entre telefone, WhatsApp, papel e planilhas. Isso permite conflitos de horário e dificulta o acompanhamento das consultas e faltas.
>
>  A solução seria criar uma **agenda centralizada**, na qual recepcionistas, profissionais e pacientes tenham diferentes níveis de acesso.
>
>  O sistema deverá controlar profissionais, pacientes, horários disponíveis e consultas, impedindo dois agendamentos para o mesmo horário. Também deverá permitir alterar o status das consultas, registrar faltas e cancelamentos e, futuramente, enviar lembretes aos pacientes.

 **Gerente:** É exatamente isso que precisamos.

 **Helder:** Então eu começaria com estas funcionalidades principais:

 1. **Cadastro de pacientes**
   - Nome
   - Telefone
   - CPF
   - Data de nascimento
2. **Cadastro de profissionais**
   - Nome
   - Especialidade
   - Horários de atendimento
3. **Agenda centralizada**
   - Visualização por dia/semana
   - Profissional
   - Horários disponíveis e ocupados
4. **Agendamento**
   - Selecionar paciente
   - Selecionar profissional
   - Selecionar data e horário
   - Definir duração
   - Impedir conflito de horários
5. **Status da consulta**
   - Agendada
   - Confirmada
   - Atendida
   - Cancelada
   - Faltou
6. **Controle de disponibilidade**
   - Criar horários
   - Bloquear horários
   - Alterar disponibilidade
7. **Acesso por usuário**
   - **Recepcionista:** gerencia pacientes e consultas.
   - **Profissional:** visualiza sua agenda e registra o atendimento/falta.
   - **Paciente:** consulta seus horários e, posteriormente, poderá realizar agendamentos.
8. **Lembretes**
   - Enviar lembrete antes da consulta.
   - Permitir confirmação ou cancelamento.

 **Gerente:** Gostei. Mas como você garantiria que duas pessoas não fossem colocadas no mesmo horário?

 **Antenor:** Eu faria essa validação no sistema antes de salvar o agendamento. Mas não confiaria somente na tela: o banco de dados também teria uma regra para impedir conflitos. Assim, mesmo que duas pessoas tentem agendar praticamente ao mesmo tempo, o sistema não permitiria que o mesmo profissional tivesse dois atendimentos conflitantes.

 **Gerente:** E se a recepcionista estiver usando o sistema e o profissional também estiver alterando a agenda?

 **Willians:** O sistema deve trabalhar com os dados centralizados. Quando alguém consultar ou alterar a agenda, estará trabalhando sobre a mesma fonte de dados. Também podemos registrar quem fez cada alteração, para termos um histórico.

 **Gerente:** Isso seria importante. Às vezes precisamos saber quem alterou um horário.

 **Helder:** Então eu adicionaria também um **histórico de alterações** para os agendamentos.

 **Gerente:** Perfeito. O que você faria primeiro?

 **Antenor:** Eu começaria pelo **MVP**, para resolver primeiro o problema principal:

 > **Paciente → Profissional → Data/Horário → Agendamento → Status**

 Depois acrescentaria recursos como lembretes automáticos, confirmação pelo paciente e outras integrações.

 **Gerente:** Muito bom. Pode começar a desenvolver.

 **Willians Júnior:** Antes de desenvolver, eu documentaria os requisitos e desenharia o fluxo da agenda. Assim conseguimos validar com a clínica se o sistema realmente representa o processo de vocês antes de começar a implementação.

---

 ### Resultado da entrevista

 Ao final da entrevista, o programador conseguiu transformar o problema inicial em requisitos claros:

 **Problema:**

 > Agendamentos descentralizados causam conflitos de horário e não permitem acompanhar faltas adequadamente.

 **Solução proposta:**

 > Criar um sistema de agenda centralizada para controlar pacientes, profissionais, horários e consultas.

 **Regra de negócio principal:**

 > Um profissional não pode possuir dois atendimentos que ocupem o mesmo intervalo de horário.

 **Usuários:**

 - Recepcionista
- Profissional de saúde
- Paciente

 **Funcionalidade central:**

 > Consultar disponibilidade → selecionar horário → criar agendamento → acompanhar o status da consulta.

 **Possíveis requisitos futuros:**

 - Lembretes por WhatsApp/SMS
- Confirmação automática
- Cancelamento pelo paciente
- Relatório de faltas
- Histórico de alterações
- Agendamento online pelo paciente
