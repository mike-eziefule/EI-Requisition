from pydantic import BaseModel
from typing import List


# Pydantic model to handle the input form data
class LineItemInput(BaseModel):
    item_name: str
    quantity: int
    category: str
    item_reason: str

class RequisitionInput(BaseModel):
    request_number: str
    description: str
    line_items: List[LineItemInput]

# Pydantic model for updating requisition status
class StatusUpdate(BaseModel):
    requisition_id: int
    status: str  # "approved" or "denied"