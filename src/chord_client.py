import requests

from requests.models import Response

CON_TIMEOUT = 3
READ_TIMEOUT = 10


def get_status(node: str) -> Response:
    return requests.get(f"http://{node}/status", timeout=(CON_TIMEOUT, READ_TIMEOUT))


def get_predecessor(node: str) -> Response:
    return requests.get(
        f"http://{node}/predecessor", timeout=(CON_TIMEOUT, READ_TIMEOUT)
    )


def get_value(node: str, key: str) -> Response:
    return requests.get(
        f"http://{node}/value/{key}", timeout=(CON_TIMEOUT, READ_TIMEOUT)
    )


def find_successor(node: str, id: int) -> Response:
    return requests.get(
        f"http://{node}/find_successor/{id}", timeout=(CON_TIMEOUT, READ_TIMEOUT)
    )


def notify(node: str, predecessor: str) -> Response:
    return requests.put(
        f"http://{node}/notify", data=predecessor, timeout=(CON_TIMEOUT, READ_TIMEOUT)
    )


def set_value(node: str, key: str, value: str) -> Response:
    return requests.put(
        f"http://{node}/value/{key}", data=value, timeout=(CON_TIMEOUT, READ_TIMEOUT)
    )
