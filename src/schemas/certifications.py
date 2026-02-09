from pydantic import BaseModel


class CertificationCreate(BaseModel):
    name: str


class CertificationRead(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
