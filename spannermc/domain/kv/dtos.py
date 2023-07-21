from litestar.contrib.sqlalchemy.dto import SQLAlchemyDTO

from spannermc.domain.kv.models import KVStore
from spannermc.lib import dto


class KeyValueStoreDTO(SQLAlchemyDTO[KVStore]):
    config = dto.config(
        max_nested_depth=0,
    )


class KVStoreCreateDTO(SQLAlchemyDTO[KVStore]):
    config = dto.config(
        include={"key", "value"},
        max_nested_depth=0,
    )


class KVStoreUpdateDTO(SQLAlchemyDTO[KVStore]):
    config = dto.config(
        include={"value"},
        max_nested_depth=0,
    )
