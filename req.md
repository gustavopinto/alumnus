# Requisitos do MVP

## 1. Objetivo

Construir um sistema web para cadastro e visualização de alunos em formato de grafo interativo. O foco do MVP é permitir que o professor cadastre alunos e relações acadêmicas, visualize a rede e reorganize visualmente os nós por clique e arraste.

## 2. Escopo do MVP

O sistema deve permitir:

- cadastrar alunos
- editar alunos
- remover ou inativar alunos
- cadastrar relações entre alunos
- visualizar os alunos em um grafo interativo
- arrastar nós no grafo para reorganização visual
- salvar a posição dos nós
- exibir foto, nome e status acadêmico no nó
- representar o status do aluno por cor

Mudanças estruturais do grafo devem ocorrer apenas via cadastro. O arraste do nó altera somente a posição visual.

## 3. Perfis de usuário

### 3.1 Administrador
Usuário responsável por cadastrar, editar e remover alunos e relações.

## 4. Requisitos funcionais

### RF01. Cadastro de aluno
O sistema deve permitir cadastrar um aluno com os seguintes campos mínimos:
- nome
- foto
- status acadêmico
- e-mail, opcional
- orientador, opcional
- observações, opcional

### RF02. Edição de aluno
O sistema deve permitir editar os dados de um aluno já cadastrado.

### RF03. Inativação de aluno
O sistema deve permitir marcar um aluno como inativo, sem apagar seus dados do banco.

### RF04. Cadastro de relações
O sistema deve permitir cadastrar relações entre alunos.

Tipos mínimos de relação:
- orienta
- coautor
- mesmo projeto
- mesmo laboratório

### RF05. Edição e remoção de relações
O sistema deve permitir editar ou remover relações cadastradas.

### RF06. Visualização em grafo
O sistema deve exibir os alunos e suas relações em formato de grafo.

### RF07. Nó customizado
Cada nó do grafo deve exibir:
- foto do aluno
- nome do aluno
- cor visual associada ao status

### RF08. Cores por status
O sistema deve usar cores distintas para representar status acadêmico:
- graduação
- mestrado
- doutorado

### RF09. Interação no grafo
O usuário deve poder:
- clicar em nós
- arrastar nós
- aproximar e afastar zoom
- mover o canvas

### RF10. Persistência do layout
O sistema deve salvar a posição visual dos nós após movimentação manual.

### RF11. Geração do grafo a partir do cadastro
Os nós e arestas exibidos no grafo devem ser gerados a partir dos dados cadastrados no banco.

### RF12. Estrutura do grafo em JSON
O backend deve expor o grafo em formato JSON contendo:
- nodes
- edges
- positions

## 5. Requisitos não funcionais

### RNF01. Arquitetura
O sistema deve ser dividido em:
- frontend web
- backend com API REST
- banco de dados PostgreSQL

### RNF02. Repositório único
O projeto deve utilizar um único repositório contendo frontend, backend e arquivos de infraestrutura.

### RNF03. Containerização
O sistema deve ser executável via Docker.

### RNF04. Orquestração local
O sistema deve possuir `docker-compose.yml` para subir, no mínimo:
- frontend
- backend
- postgres

### RNF05. Persistência de dados
Os dados do PostgreSQL devem ser persistidos por volume Docker.

### RNF06. Configuração por ambiente
As configurações devem ser carregadas por variáveis de ambiente, com suporte a arquivo `.env`.

### RNF07. API
O backend deve expor API REST em JSON.

### RNF08. Banco de dados
O PostgreSQL deve ser a fonte de verdade para cadastro de alunos, relações e layout do grafo.

### RNF09. Layout visual
A posição dos nós pode ser armazenada em campo `jsonb` ou tabela dedicada.

### RNF10. Responsividade
A interface deve funcionar em desktop e tablet. Mobile pode ter suporte básico no MVP.

### RNF11. Manutenibilidade
O código deve ser organizado por módulos e separado por responsabilidade.

### RNF12. Logs
Backend e containers devem emitir logs básicos para facilitar diagnóstico local.

## 6. Stack tecnológica

### Frontend
- React
- React Flow
- Tailwind CSS

### Backend
- Python
- FastAPI

### Banco
- PostgreSQL

### Infra
- Docker
- Docker Compose

## 7. Estrutura mínima de dados

### 7.1 Aluno
Campos mínimos:
- id
- nome
- photo_url
- status
- email
- orientador_id
- observacoes
- ativo
- created_at
- updated_at

### 7.2 Relação
Campos mínimos:
- id
- source_student_id
- target_student_id
- relation_type
- created_at

### 7.3 Layout do grafo
Campos mínimos:
- id
- name
- layout_jsonb
- updated_at

## 8. Endpoints mínimos da API

### Alunos
- `GET /students`
- `POST /students`
- `GET /students/{id}`
- `PUT /students/{id}`
- `DELETE /students/{id}`

### Relações
- `GET /relationships`
- `POST /relationships`
- `PUT /relationships/{id}`
- `DELETE /relationships/{id}`

### Grafo
- `GET /graph`
- `PUT /graph/layout`

### Upload
- `POST /upload/photo`

## 9. Estrutura mínima do JSON do grafo

```json
{
  "nodes": [
    {
      "id": "1",
      "type": "student",
      "position": { "x": 120, "y": 80 },
      "data": {
        "name": "Aluno A",
        "photoUrl": "/uploads/a.jpg",
        "status": "mestrado"
      }
    }
  ],
  "edges": [
    {
      "id": "e1-2",
      "source": "1",
      "target": "2",
      "label": "coautor"
    }
  ]
}