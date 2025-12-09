# SGHSS Mínimo – VidaPlus

Protótipo de back-end para um **Sistema de Gestão Hospitalar e de Serviços de Saúde (SGHSS)**  
da instituição(exemplo proposto) **VidaPlus**, desenvolvido em **Python + Flask + SQLite**.

O objetivo é demonstrar o funcionamento do back-end com **autenticação**,  
**cadastro de pacientes**, **cadastro de profissionais** e **agendamento de consultas**,  
incluindo a indicação de **teleconsultas**, conforme o estudo de caso do TCC.

---

## 🎯 Objetivo do sistema

Atender a um recorte simplificado do problema:

- Cadastro e atendimento de pacientes (dados básicos + consultas).
- Gestão de profissionais de saúde (dados básicos).
- Registro de consultas (presenciais ou teleconsulta).
- Autenticação de usuários do sistema (login / signup) com JWT.
- API testável via Postman

---

## ✅ Requisitos Funcionais contemplados

**RF01 – Autenticação de Usuário**  
Permitir que um usuário se cadastre (`/auth/signup`) e faça login (`/auth/login`),  
recebendo um **token JWT** para acessar recursos protegidos.

**RF02 – Cadastro de Pacientes**  
Permitir o cadastro de pacientes, com dados básicos como nome, CPF, data de nascimento e telefone.

**RF03 – Consulta de Pacientes**  
Permitir listar todos os pacientes e consultar um paciente específico por ID.

**RF04 – Cadastro de Profissionais de Saúde**  
Permitir o cadastro de profissionais de saúde (nome, especialidade).

**RF05 – Consulta de Profissionais**  
Permitir listar todos os profissionais cadastrados.

**RF06 – Cadastro de Consultas**  
Permitir registrar consultas associando paciente e profissional, com data/hora,  
tipo de atendimento (**presencial** ou **teleconsulta**) e motivo.

**RF07 – Listagem de Consultas**  
Permitir listar consultas, com filtros por `paciente_id` e `profissional_id`.

**RF08 – Healthcheck da API**  
Permitir verificar rapidamente se a API está no ar (`/health`).

> Outros requisitos do estudo de caso (leitos, relatórios financeiros, prontuário completo, prescrições, logs de auditoria detalhados, LGPD avançada, etc.)  
> não foram implementados neste protótipo mínimo, mas podem ser estendidos a partir desta base.

---

## 🔒 Requisitos Não Funcionais contemplados (mínimo)

**RNF01 – Persistência**  
Uso de **banco de dados relacional (SQLite)** através do **SQLAlchemy**.

**RNF02 – Segurança de credenciais**  
As senhas dos usuários são armazenadas utilizando **hash** com `Flask-Bcrypt`.

**RNF03 – Autorização via JWT**  
As rotas sensíveis utilizam token **JWT** via cabeçalho `Authorization: Bearer <token>`.

**RNF04 – API REST simples**  
Arquitetura baseada em API REST, facilmente testável via **Postman** ou ferramentas similares.

**RNF05 – Simplicidade de execução**  
O sistema pode ser executado localmente com poucos comandos e sem necessidade de infraestrutura complexa.

---

## 🧱 Tecnologias utilizadas

- **Python 3**
- **Flask** (framework web)
- **Flask-SQLAlchemy** (ORM)
- **Flask-Bcrypt** (hash de senha)
- **PyJWT** (tokens JWT)
- **SQLite** (banco de dados local)

---

## 🚀 Como executar o projeto

### 1. Clonar o repositório

```bash
git clone https://github.com/seu-usuario/seu-repo.git
cd seu-repo

Criar ambiente virtual:
python -m venv .venv
# Ativar ambiente virtual
# Windows:
.venv\Scripts\activate
# Linux/Mac:
# source .venv/bin/activate

instalar dependências:
pip install -r requirements.txt

executar aplicação:
python app.py

API disponível em:
http://127.0.0.1:5000
