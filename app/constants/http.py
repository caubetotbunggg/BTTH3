from enum import IntEnum


class HTTP_STATUS(IntEnum):
    INTERNAL_SERVER_ERROR = 500
    NO_CONTENT = 204
    OK = 200
    BAD_REQUEST = 400
    GATEWAY_TIMEOUT = 504
