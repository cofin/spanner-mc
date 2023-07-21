"""KeyValueStore Controllers."""
from __future__ import annotations

from typing import TYPE_CHECKING

from litestar import Controller, delete, get, patch, post
from litestar.di import Provide
from litestar.params import Dependency, Parameter

from spannermc.domain import urls
from spannermc.domain.kv.dependencies import provides_kv_service
from spannermc.domain.kv.dtos import KeyValueStoreDTO, KVStoreCreateDTO, KVStoreUpdateDTO
from spannermc.domain.kv.models import KVStore
from spannermc.domain.kv.services import KVStoreService
from spannermc.lib import log

__all__ = ["KVStoreController"]


if TYPE_CHECKING:
    from uuid import UUID

    from litestar.contrib.repository.filters import LimitOffset
    from litestar.dto import DTOData
    from litestar.pagination import OffsetPagination


logger = log.get_logger()


class KVStoreController(Controller):
    """KeyValueStore Controller."""

    tags = ["Key Value"]
    dependencies = {"kv_service": Provide(provides_kv_service)}
    signature_namespace = {"KeyValueStoreService": KVStoreService, "KeyValueStore": KVStore}
    return_dto = KeyValueStoreDTO

    @get(
        operation_id="ListKeyValueStores",
        title="List Keys",
        name="kv:list",
        summary="List KeyValueStores",
        description="Retrieve the kv.",
        path=urls.KV_LIST,
        sync_to_thread=False,
    )
    def list_kv(
        self, kv_service: KVStoreService, limit_offset: LimitOffset = Dependency(skip_validation=True)
    ) -> OffsetPagination[KVStore]:
        """List kv."""
        results, total = kv_service.list_and_count(*[limit_offset])
        return kv_service.to_dto(results, total, *[limit_offset])

    @get(
        operation_id="GetKeyValueStore",
        title="Get Key",
        name="kv:get",
        path=urls.KV_DETAIL,
        summary="Retrieve the details of a kv.",
        sync_to_thread=False,
    )
    def get_kv(
        self,
        kv_service: KVStoreService,
        kv_key: UUID = Parameter(
            title="KeyValueStore ID",
            description="The kv to retrieve.",
        ),
    ) -> KVStore:
        """Get a kv."""
        db_obj = kv_service.get_one(key=kv_key)
        return kv_service.to_dto(db_obj)

    @post(
        operation_id="CreateKeyValueStore",
        title="Create Key",
        name="kv:create",
        summary="Create a new kv.",
        cache_control=None,
        description="A kv.",
        path=urls.KV_CREATE,
        sync_to_thread=False,
        dto=KVStoreCreateDTO,
    )
    def create_kv(
        self,
        kv_service: KVStoreService,
        data: DTOData[KVStore],
    ) -> KVStore:
        """Create a new kv."""
        obj = data.create_instance()
        db_obj = kv_service.create(obj)
        return kv_service.to_dto(db_obj)

    @patch(
        operation_id="UpdateKeyValueStore",
        title="Update Key",
        name="kv:update",
        path=urls.KV_UPDATE,
        sync_to_thread=False,
        dto=KVStoreUpdateDTO,
    )
    def update_kv(
        self,
        data: DTOData[KVStore],
        kv_service: KVStoreService,
        kv_key: str = Parameter(
            title="Key value",
            description="The kv key to update.",
        ),
    ) -> KVStore:
        """Create a new kv."""
        db_obj = kv_service.get_one(key=kv_key)
        db_obj = kv_service.update(db_obj.id, data.create_instance())
        return kv_service.to_dto(db_obj)

    @delete(
        operation_id="DeleteKeyValueStore",
        title="Delete Key",
        name="kv:delete",
        path=urls.KV_DELETE,
        summary="Remove KeyValueStore",
        description="Removes a kv and all associated data from the system.",
        sync_to_thread=False,
        return_dto=None,
    )
    def delete_kv(
        self,
        kv_service: KVStoreService,
        kv_key: UUID = Parameter(
            title="KeyValueStore ID",
            description="The kv to delete.",
        ),
    ) -> None:
        """Delete a kv from the system."""
        _ = kv_service.delete(kv_key)
