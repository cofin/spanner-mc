from litestar.contrib.sqlalchemy.dto import SQLAlchemyDTO

from spannermc.domain.events.models import Event
from spannermc.lib import dto

# database model


class EventDTO(SQLAlchemyDTO[Event]):
    config = dto.config(
        exclude=("user"),
        max_nested_depth=0,
    )


class EventModifyDTO(SQLAlchemyDTO[Event]):
    config = dto.config(
        include=("message"),
        max_nested_depth=0,
    )
