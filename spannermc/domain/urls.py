INDEX = "/"
SITE_ROOT = "/{path:str}"
OPENAPI_SCHEMA = "/schema"
SYSTEM_HEALTH = "/health"


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
