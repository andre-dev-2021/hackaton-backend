# Hackaton Backend

Backend para projeto hackaton; integra ferramentas IBM Orchestrate e Firestore

## Stack

- **FastAPI** — Framework web assíncrono
- **Google Firestore** — Banco de dados NoSQL
- **IBM Watsonx Orchestrate** — Agente de IA conversacional
- **Pydantic** — Validação de dados

## Endpoints

### Sessão Watsonx

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/sessions` | Criar nova sessão |
| POST | `/api/v1/chat` | Enviar mensagem |
| DELETE | `/api/v1/sessions/{session_id}` | Encerrar sessão |

### Firestore (protegido por API Key)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/collections/{collection}` | Listar documentos |
| GET | `/api/v1/collections/{collection}/{doc_id}` | Buscar documento |
| POST | `/api/v1/convites` | Criar convite |
| PUT | `/api/v1/convites/{doc_id}/status` | Atualizar status |
| POST | `/api/v1/login` | Autenticar usuário |
| POST | `/api/v1/voluntarios` | Cadastrar voluntário |
| POST | `/api/v1/instituicoes` | Cadastrar instituição |
| POST | `/api/v1/eventos` | Criar evento |

## Estrutura do Projeto

```
.
├── auth.py          # Autenticação IBM Watsonx
├── main.py          # Endpoints da API
├── models.py        # Modelos Pydantic
├── repository.py    # Camada de acesso a dados
├── requirements.txt # Dependências Python
├── Dockerfile       # Containerização
└── .env             # Variáveis de ambiente (não versionar)
```

## Autoria

**André Pereira de Sá**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/andrepereirasa/)
[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/andre-dev-2021)
[![Gmail](https://img.shields.io/badge/Gmail-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:andrepereirasa100@gmail.com)