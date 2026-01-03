import asyncio
from dataclasses import dataclass
from typing import Optional

'''Houses the shared dataclasses'''

@dataclass
class CacheEntry:
    data: dict
    timestamp: float
    is_refreshing: bool = False

@dataclass
class OptionDataRequest:
    ticker: str
    option_type: str
    expiration_date: Optional[str]
    strike: Optional[float]
    future: asyncio.Future
