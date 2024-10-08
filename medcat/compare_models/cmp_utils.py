from typing import Type, TypeVar, Generic, Iterable, Callable, Optional

import sqlite3
import re
from pydantic import BaseModel


T = TypeVar('T', bound=BaseModel)


def sanitize_table_name(name, max_length=64):
    # Replace any characters not allowed in table names with underscores
    name = re.sub(r'[^a-zA-Z0-9_$]', '_', name)
    # Truncate the name if it's too long
    name = name[:max_length]
    return name


class SaveOptions(BaseModel):
    use_db: bool = False
    db_file_name: Optional[str] = None
    clean_callback: Optional[Callable[[], None]] = None


class DifferenceDatabase(Generic[T]):

    def __init__(self, db_file: str, part: str, model_type: Type[T],
                 batch_size: int = 100):
        self.db_file = db_file
        self.part = sanitize_table_name(part)
        self.model_type = model_type
        self.conn = sqlite3.connect(self.db_file)
        self.cursor = self.conn.cursor()
        self._create_table()
        self._len = 0
        self._batch_size = batch_size

    def _create_table(self):
        self.cursor.execute(f'''CREATE TABLE IF NOT EXISTS differences_{self.part}
                              (id INTEGER PRIMARY KEY, data TEXT)''')
        self.conn.commit()

    def append(self, difference: T):
        data = difference.json()
        self.cursor.execute(f"INSERT INTO differences_{self.part} (data) VALUES (?)", (data,))
        self.conn.commit()
        self._len += 1

    def __iter__(self) -> Iterable[T]:
        self.cursor.execute(f"SELECT data FROM differences_{self.part}")
        while True:
            rows = self.cursor.fetchmany(self._batch_size)
            if not rows:
                break
            for row in rows:
                yield self.model_type.parse_raw(row[0])

    def __len__(self) -> int:
        return self._len

    def __del__(self):
        self.conn.close()
