from pydantic import BaseModel as _BaseModel
from pydantic import ConfigDict

from spannermc.utils import camel_case

__all__ = ["BaseSchema", "CamelizedBaseSchema", "Message"]


class BaseSchema(_BaseModel):
    """Base Settings."""

    model_config = ConfigDict(
        validate_assignment=True,
        from_attributes=True,
        use_enum_values=True,
        arbitrary_types_allowed=True,
    )


class CamelizedBaseSchema(BaseSchema):
    """Camelized Base pydantic schema."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=camel_case)


class Message(CamelizedBaseSchema):
    """Message DTO."""

    message: str
