from typing import Optional
from pydantic import BaseModel, ConfigDict


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    file_url: str
    uploaded_by: int
    department: Optional[str] = None
