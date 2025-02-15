from enum import Enum

from dataclasses import dataclass

class StatusCode(Enum):
    TOKEN_SUCCESS = 000
    IGDB_GAME_FOUND = 100
    IGDB_ERROR = 120
    IGDB_ERROR_REQUEST = 121
    IGDB_ERROR_TIMEOUT = 122
    IGDB_ERROR_GAME_NOT_FOUND = 124
    IGDB_WARN = 110
    NOTION_ERROR = 2
    NOTION_WARN = 22
    HLTB_ERROR = 3
    HLTB_WARN= 33
    OS_ERROR= 4

@dataclass
class Status:
    code: StatusCode
    message: str

    def __str__(self):
        return f"{"!" if self.code != StatusCode.SUCCESS else "✔"} {self.message}"