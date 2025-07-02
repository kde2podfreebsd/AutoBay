from dataclasses import dataclass
from datetime import datetime

@dataclass
class Order:
    id: int
    user_id: int
    username: str
    type: str
    data: str
    status: str
    payment_status: str
    created_at: datetime