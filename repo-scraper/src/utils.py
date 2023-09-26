from dataclasses import asdict, is_dataclass
import datetime
import json
from typing import Any, Dict, List, Union

from flask import make_response, Response
import shortuuid


class SearchNames:
    """Keeps a record of the names used for sources and analyzers during
    a search.

    """
    def __init__(self) -> None:
        self.source_names: List[str] = []
        self.analyzer_names: List[str] = []

    def generate_source_name(self) -> str:
        """Generates a short UUID for a new source name and stores it.

        Returns:
            The generated and stored UUID.

        """
        uuid = shortuuid.uuid()
        self.source_names.append(uuid)
        return uuid

    def generate_analyzer_name(self) -> str:
        """Generates a short UUID for a new analyzer name and stores it.

        Returns:
            The generated and stored UUID.

        """
        uuid = shortuuid.uuid()
        self.analyzer_names.append(uuid)
        return uuid


class ExtendedEncoder(json.JSONEncoder):
    """Extended JSON serializer, allowing for dates, datetimes, and
    dataclasses.

    """
    def default(self, obj: Any) -> Union[str, int, List, Dict]:
        """Returns the serialized form of the object.

        Args:
            obj: The object to be serialized.

        Returns:
            The object in its serialized form.
        """
        if isinstance(obj, datetime.datetime):
            return str(obj)

        elif isinstance(obj, datetime.date):
            return str(obj)

        elif is_dataclass(obj):
            return asdict(obj)

        return json.JSONEncoder.default(self, obj)


def create_response(data: Any, code: int, headers=None) -> Response:
    """Creates a response from the provided return data and return code.

    Args:
        data: The data to be returned to the client.
        code: The return code for the API response.
        headers: The HTTP headers for the response.

    Returns:
        The response from the provided constituent parts.

    """
    dumped = json.dumps(data, cls=ExtendedEncoder)
    resp = make_response(dumped, code)
    resp.headers.extend(headers or {})

    return resp
