from pydantic import BaseModel as _BaseModel

from spannermc.utils import camel_case

__all__ = ["BaseSchema", "CamelizedBaseSchema", "Message"]


class BaseSchema(_BaseModel):
    """Base Settings."""

    class Config:
        """Base Settings Config."""

        case_sensitive = False
        validate_assignment = True
        orm_mode = True
        use_enum_values = True
        arbitrary_types_allowed = True


class CamelizedBaseSchema(BaseSchema):
    """Camelized Base pydantic schema."""

    class Config:
        """Camel Case config."""

        allow_population_by_field_name = True
        alias_generator = camel_case


class Message(CamelizedBaseSchema):
    """Message DTO."""

    message: str
