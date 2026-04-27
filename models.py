from pydantic import BaseModel
from datetime import datetime

# FIRESTORE COLLECTION MODELS

class Convite(BaseModel):
    uid_voluntario: str
    nome_instituicao: str
    titulo_evento: str
    horario_evento: datetime
    
class Login(BaseModel):
    email: str
    password: str
    
class Cadastro(BaseModel):
    nome: str
    email: str
    password: str
    tipo: str
    
class Voluntario(BaseModel):
    nome: str
    logradouro: str
    cidade: str
    uf: str
    cep: str
    contato: str
    habilidades: list[str]
    disponibilidade: list[str]
    
class Instituicao(BaseModel):
    nome: str
    setor: str
    logradouro: str
    numero: int
    cidade: str
    uf: str
    cep: str
    contato: str
    
class Evento(BaseModel):
    titulo_evento: str
    instituicao: str
    horario_evento: str
    n_participantes: int
    participantes: list[str]
    status: str

# IBM WO CHAT MODELS 

class StartSessionResponse(BaseModel):
    session_id: str

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    session_id: str
    response: str