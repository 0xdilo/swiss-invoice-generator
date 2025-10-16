from pydantic import BaseModel

class Client(BaseModel):
    id: int | None = None
    name: str
    address: str
    cap: str
    city: str
    nation: str
    email: str

class Invoice(BaseModel):
    id: int | None = None
    client_id: int
    template_id: int
    data: dict  

class Template(BaseModel):
    id: int | None = None
    name: str
    filename: str

