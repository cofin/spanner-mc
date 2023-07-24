INDEX = "/"
SITE_ROOT = "/{path:str}"
OPENAPI_SCHEMA = "/schema"


ACCOUNT_LOGIN = "/api/access/login"
ACCOUNT_REGISTER = "/api/access/signup"
ACCOUNT_PROFILE = "/api/me"
ACCOUNT_LIST = "/api/users"
ACCOUNT_DELETE = "/api/users/{user_id:uuid}"
ACCOUNT_DETAIL = "/api/users/{user_id:uuid}"
ACCOUNT_UPDATE = "/api/users/{user_id:uuid}"
ACCOUNT_CREATE = "/api/users"


EVENT_LIST = "/api/events"
EVENT_DELETE = "/api/events/{event_id:uuid}"
EVENT_DETAIL = "/api/events/{event_id:uuid}"
EVENT_UPDATE = "/api/events/{event_id:uuid}"
EVENT_CREATE = "/api/events"


KV_LIST = "/api/kv"
KV_DELETE = "/api/kv/{kv_key:str}"
KV_DETAIL = "/api/kv/{kv_key:str}"
KV_UPDATE = "/api/kv/{kv_key:str}"
KV_CREATE = "/api/kv"
