from pydantic import BaseModel
import requests

import csv
import json
from pathlib import Path
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Tuple,
    TypeVar,
    Type,
    Union,
)
T = TypeVar('T', bound=BaseModel)


def exception_on_error_code(func):
    """
    Decorator for methods returning `requests.Result`. The decorator raises a
    `requests.exceptions.HTTPError` error containing a comprehensive error
    description containing the response body. This is needed as NocoDB writes
    most of the error description into the body part.

    This method resembles the `requests.models.Model.raise_for_status` method.
    """
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)

        if 400 <= response.status_code < 500:
            kind = "Client Error"
        elif 500 <= response.status_code < 600:
            kind = "Server Error"
        else:
            return response

        if isinstance(response.reason, bytes):
            try:
                reason = response.reason.decode('utf-8')
            except UnicodeDecodeError:
                reason = response.reason.decode('iso-8859-1')
        else:
            reason = response.reason

        if "msg" in response.json():
            message = f", {response.json()['msg']}"

        msg = f"{response.status_code} {kind} {reason} for url {response.url}{message}"
        raise requests.exceptions.HTTPError(
            msg,
            response=response,
        )
    return wrapper


class Client(Generic[T]):
    """
    Generic NocoDB REST API client using data models defined with
    `pydantic.BaseModel` to enable a straightforward interaction with your
    NocoDB data sets.
    """

    base_url: str
    """Base URL of the NocoDB API."""
    auth_token: str
    """JWT authentication token."""

    def __init__(
        self,
        base_url: str,
        auth_token: str,
    ):
        self.base_url = base_url
        self.auth_token = auth_token

    # API IMPLEMENTATION

    def add(self, item: Union[T, List[T]]):
        """
        Insert a single or multiple row(s) into the table.
        """
        self.__post(item, self.base_url)

    def import_csv(self, path: Path):
        """
        Import records from a CSV file. The first row has to contain the names
        of the fields as described in the type model.
        """
        ttype = self._type()
        with open(path) as f:
            data = csv.DictReader(f)
            items = []
            for entry in data:
                if "id" not in entry:
                    entry["id"] = -1
                items.append(ttype.parse_obj(entry))
        self.add(items)

    def list(
        self,
        where: Union[None, str] = None,
        limit: int = 10,
        offset: int = 0,
        sort: Union[None, str, List[str]] = None,
        fields: Union[None, str, List[str]] = None,
        fields1: Union[None, str, List[str]] = None,
    ) -> List[T]:
        """
        Get a list of all items applying to the optional parameters. Learn more
        on the query parameters [here](https://docs.nocodb.com/developer-resour
        ces/rest-apis#query-params).

        where
            Complicated where conditions.
        limit
            Number of rows to get(SQL limit value).
        offset
            Offset for pagination(SQL offset value).
        sort
            Sort by column name, Use `- a` prefix for descending sort.
        fields
            Required column names in result.
        fields1
            Required column names in child result.
        """
        params = {
            "limit": limit,
            "offset": offset,
        }
        if where is not None:
            params["where"] = where
        if sort is not None:
            if isinstance(sort, List[str]):
                sort = ",".join(sort)
            params["sort"] = sort
        if fields is not None:
            if isinstance(fields, List[str]):
                fields = ",".join(fields)
            params["fields"] = fields
        if fields1 is not None:
            if isinstance(fields1, List[str]):
                fields1 = ",".join(fields1)
            params["fields1"] = fields1

        rsp = self.__get(params, self.base_url)
        rsl = []
        for item in rsp.json():
            rsl.append(self._type().parse_obj(item))
        return rsl

    def by_id(self, id: int) -> T:
        """Return a item with the given id."""
        rsp = self.__get(self.base_url, str(id))
        if "id" not in rsp.json():
            raise KeyError(f"no item found for id {id}")
        return self._type().parse_obj(rsp.json())

    def update(self, id: int, item: Union[Dict[str, Any], T]):
        """
        Update a item. Accepts a whole pydantic model of the item or a dict
        mapping the name of the field to the desired new value.
        """
        self.__put(item, self.base_url, str(id))

    def delete(self, id: int):
        """Delete a item with a given id."""
        self.__delete(self.base_url, str(id))

    # HELPER METHODS

    def _type(self) -> Type:
        """Returns the type of the generic T."""
        return self.__orig_class__.__args__[0]

    # HANDLING REQUESTS

    @exception_on_error_code
    def __delete(
        self,
        *url: Tuple[str],
    ) -> requests.Response:
        """Send a DELETE request to the API."""
        return requests.delete(
            self.__build_url(*url),
            headers={
                "xc-auth": self.auth_token,
                "accept": "application/json",
            },
        )

    @exception_on_error_code
    def __get(
        self,
        params: Dict[str, Any] = {},
        *url: Tuple[str],
    ) -> requests.Response:
        """Send a GET request to the API and returns the result."""
        return requests.get(
            self.__build_url(*url),
            headers={"xc-auth": self.auth_token},
            params=params,
        )

    @exception_on_error_code
    def __post(
        self,
        payload: Union[T, List[T]],
        *url: Tuple[str],
    ) -> requests.Response:
        """
        Send a POST request with the given payload to the URL.
        """
        if isinstance(payload, self._type()):
            payload = payload.json(exclude={"id"})
        else:
            url = (*url, "bulk")
            items = []
            for item in payload:
                items.append(item.dict(exclude={"id"}))
            payload = json.dumps(items)
        return requests.post(
            self.__build_url(*url),
            headers={
                "xc-auth": self.auth_token,
                "accept": "application/json",
                "Content-Type": "application/json",
            },
            data=payload,
        )

    @exception_on_error_code
    def __put(
        self,
        payload: Union[Dict[str, Any], T],
        *url: Tuple[str],
    ) -> requests.Response:
        """
        Send a PUT request with the given payload to the URL.
        """
        if isinstance(payload, self._type()):
            payload = payload.json(exclude={"id"})
        else:
            payload = json.dumps(payload)
        return requests.put(
            self.__build_url(*url),
            headers={
                "xc-auth": self.auth_token,
                "accept": "application/json",
                "Content-Type": "application/json",
            },
            data=payload,
        )

    @staticmethod
    def __build_url(*args: Tuple[str]) -> str:
        """Conceits multiple strings to a valid url. Handles the slashes."""
        rsl = []
        for part in args:
            if len(part) == 0:
                continue
            if part[0] == "/":
                part = part[1:]
            if part[-1] == "/":
                part = part[:-1]
            if len(part) != 0:
                rsl.append(part)
        return "/".join(rsl)
