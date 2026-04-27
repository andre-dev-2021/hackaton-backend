import os
import httpx
import re
import json
from fastapi import FastAPI, HTTPException, Depends
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Security
from google.cloud import firestore
from auth import INSTANCE_URL, get_token
from repository import Repository
from models import ChatRequest, ChatResponse, Convite, Instituicao, Login, StartSessionResponse, Voluntario, Evento

def parse_logs_to_json(text):
    pattern = r'\{.*?\}(?=\n|$)'
    matches = re.findall(pattern, text)

    result = []
    for item in matches:
        clean = item.replace('\\"', '"')
        result.append(json.loads(clean))

    return result

def join_messages(events):
    parts = []

    for item in events:
        if item.get("event") == "message.delta":
            delta = item.get("data", {}).get("delta", {})
            contents = delta.get("content", [])

            for c in contents:
                if c.get("response_type") == "text":
                    parts.append(c.get("text", ""))

    return "".join(parts)
    
    
load_dotenv()

app = FastAPI(
    title="Hackaton Backend API",
    description="API REST para gerenciamento de voluntários, instituições e eventos de hackathon social.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET, POST, PUT, DELETE"],
    allow_headers=["*"],
)

# IBM Watsonx Orchestrate integration 

@app.post("/api/v1/sessions", response_model=StartSessionResponse)
async def create_session():
    """Cria uma nova sessão (thread) no Watsonx Orchestrate."""
    token = await get_token()
    async with httpx.AsyncClient(timeout=60) as client:
        res = await client.post(
            f"{INSTANCE_URL}/v1/orchestrate/runs?stream=true&stream_timeout=120000&multiple_content=true",
            headers={
                "Authorization": f"Bearer {token}",
                "IAM-API_KEY": os.getenv("WO_API_KEY"),
                "accept": "application/json",
                "Content-Type": "application/json",
            },
            json={
                "message": {
                    "role": "user",
                    "content": "ola"
                },
                "agent_id": os.getenv("WO_AGENT_ID"),
            },
        )
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail=res.text)
        res = parse_logs_to_json(res.text)
        thread_id = res[0].get("data").get("thread_id")

    return {"session_id": thread_id}


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(body: ChatRequest):
    """Envia uma mensagem para o agente e retorna a resposta."""
    token = await get_token()
    async with httpx.AsyncClient(timeout=120) as client:
        res = await client.post(
            f"{INSTANCE_URL}/v1/orchestrate/runs?stream=true&stream_timeout=120000&multiple_content=true",
            headers={
                "Authorization": f"Bearer {token}",
                "IAM-API_KEY": os.getenv("WO_API_KEY"),
                "accept": "application/json",
                "Content-Type": "application/json",
            },
            json={
                "message": {
                    "role": "user",
                    "content": body.message
                },
                "agent_id": os.getenv("WO_AGENT_ID"),
                "thread_id": body.session_id,  # Usa a thread_id da sessão
            },
        )
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail=res.text)
        res = parse_logs_to_json(res.text)
        msg = join_messages(res)

    # Retorna a thread_id atualizada
    thread_id = res[0].get("data").get("thread_id") or body.session_id

    return {"session_id": thread_id, "response": msg}


@app.delete("/api/v1/sessions/{session_id}")
async def close_session(session_id: str):
    """Encerra uma sessão."""
    token = await get_token()
    async with httpx.AsyncClient() as client:
        res = await client.delete(
            f"{INSTANCE_URL}/v1/chat/sessions/{session_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
    return {"closed": session_id, "status": res.status_code}

# Handle database operations

repository = Repository()

API_KEY = os.getenv("API_KEY")
api_key_header = APIKeyHeader(name="X-API-Key")

def verificar_chave(key: str = Security(api_key_header)):
    if key != API_KEY:
        raise HTTPException(status_code=403, detail="Chave inválida")
    
@app.get("/api/v1/collections/{collection_name}", dependencies=[Depends(verificar_chave)])
def get_collection(collection_name: str):
    data = repository.get_collection(collection_name)
    return data

@app.get("/api/v1/collections/{collection_name}/{doc_id}", dependencies=[Depends(verificar_chave)])
def get_document(collection_name: str, doc_id: str):
    data = repository.get_document(collection_name, doc_id)
    return data

@app.post("/api/v1/convites", dependencies=[Depends(verificar_chave)], status_code=201)
def criar_convite(c: Convite):
    data = {
        "uid_voluntario": c.uid_voluntario,
        "nome_instituicao": c.nome_instituicao,
        "titulo_evento": c.titulo_evento,
        "horario_evento": c.horario_evento.isoformat(),
        "criado_em": firestore.SERVER_TIMESTAMP,
        "status": "pendente"  # campo útil para o agente filtrar depois
    }
    
    repository.set_document("convites", data)
    return {
        "message": "Convite criado com sucesso"
    }

@app.put("/api/v1/convites/{doc_id}/status", dependencies=[Depends(verificar_chave)])
def update_convite_status(doc_id: str, status: str):
    status_validos = ["pendente", "aceito", "rejeitado", "cancelado"]
    
    if status not in status_validos:
        raise HTTPException(status_code=400, detail=f"Status inválido. Use: {', '.join(status_validos)}")
    
    repository.update_document("convites", {"status": status}, doc_id)
    return {
        "message": "Status do convite atualizado com sucesso"
    }
    
@app.post("/api/v1/login", dependencies=[Depends(verificar_chave)])
def login(login: Login):
    user = [u for u in repository.get_collection('usuarios') if u["email"] == login.email][0]
    
    if(user == []):
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    if(user['senha'] != login.password):
        raise HTTPException(status_code=401, detail="Senha inválida")
    
    return {
        "id": user['id'],
        "email": user['email'],
        "tipo": user['tipo']
    }

@app.post("/api/v1/voluntarios", dependencies=[Depends(verificar_chave)], status_code=201)
def set_voluntario(v: Voluntario):
    data = {
        "nome": v.nome,
        "logradouro": v.logradouro,
        "cidade": v.cidade,
        "uf": v.uf,
        "cep": v.cep,
        "contato": v.contato,
        "habilidades": v.habilidades,
        "disponibilidade": v.disponibilidade
    }
    
    repository.set_document("voluntarios", data)
    return {
        "message": "Novo voluntario adicionado com sucesso"
    }
    
    
@app.put("/api/v1/voluntarios/{doc_id}", dependencies=[Depends(verificar_chave)])
def update_voluntario(v: Voluntario, doc_id: str):
    data = {
        "nome": v.nome,
        "logradouro": v.logradouro,
        "cidade": v.cidade,
        "uf": v.uf,
        "cep": v.cep,
        "contato": v.contato,
        "habilidades": v.habilidades,
        "disponibilidade": v.disponibilidade
    }
    repository.update_document("voluntarios", data, doc_id)
    return {
        "message": "Voluntario atualizado com sucesso"
    }
    
@app.delete("/api/v1/voluntarios/{doc_id}", dependencies=[Depends(verificar_chave)])
def delete_voluntario(doc_id: str):
    repository.delete_document(doc_id)
    return {
        "message": "Voluntario apagado com sucesso"
    }
    
@app.post("/api/v1/instituicoes", dependencies=[Depends(verificar_chave)], status_code=201)
def set_instituicao(i: Instituicao):
    data = {
        "nome": i.nome,
        "setor": i.setor,
        "logradouro": i.logradouro,
        "numero": i.numero,
        "cidade": i.cidade,
        "uf": i.uf,
        "cep": i.cep,
        "contato": i.contato
    }
    repository.set_document("instituicoes", data)
    return {
        "message": "Nova instituição adicionado com sucesso"
    }
        
@app.put("/api/v1/instituicoes/{doc_id}", dependencies=[Depends(verificar_chave)])
def update_instituicao(i: Instituicao, doc_id: str):
    data = {
        "nome": i.nome,
        "setor": i.setor,
        "logradouro": i.logradouro,
        "numero": i.numero,
        "cidade": i.cidade,
        "uf": i.uf,
        "cep": i.cep,
        "contato": i.contato
    }
    repository.update_document("instituicoes", data, doc_id)
    return {
        "message": "Instituicão atualizada com sucesso"
    }
    
    
@app.delete("/api/v1/instituicoes/{doc_id}", dependencies=[Depends(verificar_chave)])
def delete_instituicao(doc_id: str):
    repository.delete_document(doc_id)
    return {
        "message": "Instituicao apagada com sucesso"
    }

@app.post("/api/v1/eventos", dependencies=[Depends(verificar_chave)], status_code=201)
def criar_evento(e: Evento):
    data = {
        "titulo_evento": e.titulo_evento,
        "instituicao": e.instituicao,
        "horario_evento": e.horario_evento,
        "n_participantes": e.n_participantes,
        "participantes": e.participantes,
        "status": e.status
    }
    repository.set_document("eventos", data)
    return {
        "message": "Evento criado com sucesso"
    }

@app.get("/api/v1/eventos", dependencies=[Depends(verificar_chave)])
def listar_eventos():
    return repository.get_collection("eventos")

@app.get("/api/v1/eventos/{doc_id}", dependencies=[Depends(verificar_chave)])
def get_evento(doc_id: str):
    data = repository.get_document("eventos", doc_id)
    if not data:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    return data

@app.put("/api/v1/eventos/{doc_id}", dependencies=[Depends(verificar_chave)])
def update_evento(e: Evento, doc_id: str):
    data = {
        "titulo_evento": e.titulo_evento,
        "instituicao": e.instituicao,
        "horario_evento": e.horario_evento,
        "n_participantes": e.n_participantes,
        "participantes": e.participantes,
        "status": e.status
    }
    repository.update_document("eventos", data, doc_id)
    return {
        "message": "Evento atualizado com sucesso"
    }

@app.delete("/api/v1/eventos/{doc_id}", dependencies=[Depends(verificar_chave)])
def delete_evento(doc_id: str):
    repository.delete_document("eventos", doc_id)
    return {
        "message": "Evento apagado com sucesso"
    }