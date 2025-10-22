import requests
from requests.models import Response

CON_TIMEOUT = 3
READ_TIMEOUT = 10


def get_status(node: str) -> Response | None:
    try:
        return requests.get(
            f"http://{node}/status", timeout=(CON_TIMEOUT, READ_TIMEOUT)
        )
    except requests.exceptions.RequestException:
        return None


def get_predecessor(node: str) -> Response | None:
    try:
        return requests.get(
            f"http://{node}/predecessor", timeout=(CON_TIMEOUT, READ_TIMEOUT)
        )
    except requests.exceptions.RequestException:
        return None


def get_value(node: str, key: str) -> Response | None:
    try:
        return requests.get(
            f"http://{node}/value/{key}", timeout=(CON_TIMEOUT, READ_TIMEOUT)
        )
    except requests.exceptions.RequestException:
        return None


def get_successor_list(node: str) -> Response | None:
    try:
        return requests.get(
            f"http://{node}/successor_list", timeout=(CON_TIMEOUT, READ_TIMEOUT)
        )
    except requests.exceptions.RequestException:
        return None


def find_successor(node: str, id: int) -> Response | None:
    try:
        return requests.get(
            f"http://{node}/find_successor/{id}", timeout=(CON_TIMEOUT, READ_TIMEOUT)
        )
    except requests.exceptions.RequestException:
        return None


def notify(node: str, predecessor: str) -> Response | None:
    try:
        return requests.put(
            f"http://{node}/notify",
            data=predecessor,
            timeout=(CON_TIMEOUT, READ_TIMEOUT),
        )
    except requests.exceptions.RequestException:
        return None


def set_value(node: str, key: str, value: str) -> Response | None:
    try:
        return requests.put(
            f"http://{node}/value/{key}",
            data=value,
            timeout=(CON_TIMEOUT, READ_TIMEOUT),
        )
    except requests.exceptions.RequestException:
        return None


def set_successor(node: str, successor: str) -> Response | None:
    try:
        return requests.put(
            f"http://{node}/successor",
            data=successor,
            timeout=(CON_TIMEOUT, READ_TIMEOUT),
        )
    except requests.exceptions.RequestException:
        return None


def set_predecessor(node: str, predecessor: str) -> Response | None:
    try:
        return requests.put(
            f"http://{node}/predecessor",
            data=predecessor,
            timeout=(CON_TIMEOUT, READ_TIMEOUT),
        )
    except requests.exceptions.RequestException:
        return None
