from pydantic import BaseModel, validator
from typing import List, Optional, Union


# Pydantic model to handle the input form data
class LineItemInput(BaseModel):
    id: Optional[int]  # Optional ID for existing line items
    item_name: str
    quantity: int
    category: str
    item_reason: str

class RequisitionInput(BaseModel):
    request_number: str
    description: str
    line_items: List[LineItemInput]  # List of line items

class ExpenseLineItemInput(BaseModel):
    id: Optional[int]  # Optional ID for existing line items
    item_name: str
    quantity: Union[int, float]
    category: str
    price: Union[int, float]
    amount: Union[int, float]

    @validator("quantity", "price", "amount", pre=True)
    def parse_numeric(cls, v):
        if isinstance(v, str):
            try:
                if "." in v:
                    return float(v)
                return int(v)
            except Exception:
                raise ValueError("Must be a number")
        return v

class ExpenseInput(BaseModel):
    expense_number: str
    description: str
    line_items: List[ExpenseLineItemInput]
    total: Union[int, float]

    @validator("total", pre=True)
    def parse_total(cls, v):
        if isinstance(v, str):
            try:
                if "." in v:
                    return float(v)
                return int(v)
            except Exception:
                raise ValueError("Total must be a number")
        return v

# Pydantic model for updating requisition status
class StatusUpdate(BaseModel):
    requisition_id: int
    status: str  # "approved" or "denied"