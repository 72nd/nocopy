from pydantic import BaseModel
import requests

import csv
import datetime
import json
from pathlib import Path
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
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

        try:
            if "msg" in response.json():
                message = f", {response.json()['msg']}"
        except json.decoder.JSONDecodeError:
            message = f":\n{response._content.decode()}"

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

    If the generic type `T` is not set the class handles the data as a simple
    dict and omits any checks.
    """

    base_url: str
    """Base URL of the NocoDB API."""
    auth_token: str
    """JWT authentication token."""
    debug: bool

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
        with open(path) as f:
            data = csv.DictReader(f)

            if self._type() is not None:
                items = []
                for entry in data:
                    if "id" not in entry:
                        entry["id"] = -1
                    items.append(self._type().parse_obj(entry))
                self.add(items)
            else:
                self.add(data)

    def list(
        self,
        where: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        sort: Union[None, str, List[str]] = None,
        fields: Union[None, str, List[str]] = None,
        fields1: Union[None, str, List[str]] = None,
        as_dict: bool = False,
    ) -> Union[List[Dict], List[T]]:
        """
        Get a list of all items applying to the optional parameters. Learn more
        on the query parameters [here](https://docs.nocodb.com/developer-resour
        ces/rest-apis#query-params).

        where
            Complicated where conditions.
        limit
            Number of rows to get(SQL limit value). When set to `None` all
            records will be fetched by first determine the count of records
            using the `Client.count` method.
        offset
            Offset for pagination(SQL offset value).
        sort
            Sort by column name, Use `- a` prefix for descending sort.
        fields
            Required column names in result.
        fields1
            Required column names in child result.
        """
        if limit is None:
            limit = self.count()
        params = {
            "offset": offset,
            "limit": limit,
        }
        params = self.__cond_add_param(params, where, "where")
        params = self.__cond_add_param(params, sort, "sort")
        params = self.__cond_add_param(params, fields, "fields")
        params = self.__cond_add_param(params, fields1, "fields1")
        rsp = self.__get(params, self.base_url)
        return self.__build_return(rsp, as_dict)

    def by_id(self, id: int) -> T:
        """Return a item with the given id."""
        rsp = self.__get(self.base_url, str(id))
        if "id" not in rsp.json():
            raise KeyError(f"no item found for id {id}")

        if self._type() is None:
            return rsp.json()
        return self._type().parse_obj(rsp.json())

    def exists(self, id: int) -> bool:
        """Returns whether a record with the given id exists or not."""
        rsp = self.__get({}, self.base_url, str(id), "exists")
        return rsp.json()

    def update(self, id: int, item: Union[Dict[str, Any], T]):
        """
        Update a item. Accepts a whole pydantic model of the item or a dict
        mapping the name of the field to the desired new value.
        """
        self.__put(item, self.base_url, str(id))

    def bulk_update(self, items: List[T]):
        """
        Update multiple items. Dict has to contain the id of the record to
        be changed.
        """
        self.__put(items, self.base_url, exclude_id=False)

    def delete(self, id: int):
        """Delete a item with a given id."""
        self.__delete(self.base_url, str(id))

    def count(self, where: Optional[str] = None) -> int:
        """
        Count records in table. Learn more on the where query parameters [here]
        (https://docs.nocodb.com/developer-resources/rest-apis#query-params).
        """
        params = {}
        if where is not None:
            params["where"] = where
        rsp = self.__get(params, self.base_url, "count")
        return rsp.json()["count"]

    def find_first(
        self,
        where: Optional[str] = None,
        offset: int = 0,
        sort: Union[None, str, List[str]] = None,
        fields: Union[None, str, List[str]] = None,
        as_dict: bool = False,
    ) -> T:
        """
        Get first record according to given filters.

        where
            Complicated where conditions.
        offset
            Offset for pagination(SQL offset value).
        sort
            Sort by column name, Use `- a` prefix for descending sort.
        fields
            Required column names in result.
        """
        params = {
            "offset": offset,
        }
        params = self.__cond_add_param(params, where, "where")
        params = self.__cond_add_param(params, sort, "sort")
        params = self.__cond_add_param(params, fields, "fields")
        rsp = self.__get(params, self.base_url, "findOne")
        return [self.__build_return(rsp, as_dict)]

    def group_by(
        self,
        column_name: Optional[str] = None,
        where: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        sort: Union[None, str, List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get first record according to given filters.

        column_name
            Column name.
        where
            Complicated where conditions.
        limit
            Number of rows to get(SQL limit value). When set to `None` all
            records will be fetched by first determine the count of records
            using the `Client.count` method.
        offset
            Offset for pagination(SQL offset value).
        sort
            Sort by column name, Use `- a` prefix for descending sort.
        """
        if limit is None:
            limit = self.count()
        params = {
            "limit": limit,
            "offset": offset,
        }
        params = self.__cond_add_param(params, column_name, "column_name")
        params = self.__cond_add_param(params, where, "where")
        params = self.__cond_add_param(params, sort, "sort")
        rsp = self.__get(params, self.base_url, "groupby")
        return rsp.json()

    def aggregate(
        self,
        column_name: Optional[str] = None,
        func: Union[None, str, List[str]] = None,
        having: Optional[str] = None,
        fields: Union[None, str, List[str]] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        sort: Union[None, str, List[str]] = None,
        as_dict: bool = False,
    ) -> Dict[str, Any]:
        """
        Filter and aggergate records using functions.

        column_name
            Column name.
        func
            One or multiple aggregate function(s). Can be min, max, avg, sum,
            count.
        having
            Having expression.
        fields
            Fields from the model.
        limit
            Number of rows to get(SQL limit value). When set to `None` all
            records will be fetched by first determine the count of records
            using the `Client.count` method.
        offset
            Offset for pagination(SQL offset value).
        sort
            Sort by column name, Use `- a` prefix for descending sort.
        """
        if limit is None:
            limit = self.count()
        params = {
            "limit": limit,
            "offset": offset,
        }
        params = self.__cond_add_param(params, column_name, "column_name")
        params = self.__cond_add_param(params, func, "func")
        params = self.__cond_add_param(params, having, "having")
        params = self.__cond_add_param(params, fields, "fields")
        params = self.__cond_add_param(params, sort, "sort")
        rsp = self.__get(params, self.base_url, "")
        return rsp.json()

    # HELPER METHODS

    def _type(self) -> Optional[Type]:
        """
        Returns the type of the generic T. Returns `None` when no type was set
        for `T`.
        """
        if "__orig_class__" not in self.__dict__:
            return None
        return self.__orig_class__.__args__[0]

    # HANDLING REQUESTS

    @exception_on_error_code
    def __delete(
        self,
        *url: Tuple[str],
    ) -> requests.Response:
        """Send a DELETE request to the API."""
        return requests.delete(
            build_url(*url),
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
            build_url(*url),
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
        payload, url = self.__build_payload(
            payload,
            *url,
        )
        return requests.post(
            build_url(*url),
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
        exclude_id: bool = True,
    ) -> requests.Response:
        """
        Send a PUT request with the given payload to the URL.
        """
        payload, url = self.__build_payload(
            payload,
            *url,
            exclude_id=exclude_id,
        )
        return requests.put(
            build_url(*url),
            headers={
                "xc-auth": self.auth_token,
                "accept": "application/json",
                "Content-Type": "application/json",
            },
            data=payload,
        )

    def __build_payload(
        self,
        payload: Union[T, List[T]],
        *url: Tuple[str],
        exclude_id: bool = True,
    ) -> Tuple[Union[str, Tuple[str]]]:
        """Handles the different possible payloads."""
        if self._type() is not None and isinstance(payload, self._type()) and \
                exclude_id:
            # Got single BaseModel instance.
            payload = payload.json(exclude={"id"})
        elif isinstance(payload, dict):
            payload = json.dumps(payload)
        else:
            url = (*url, "bulk")
            items = []
            for item in payload:
                if isinstance(item, dict):
                    # List of dicts.
                    items.append(item)
                else:
                    # List of model instances.
                    items.append(item.dict(exclude={"id"}))
            payload = json.dumps(items, default=self.__json_converter)
        return (payload, url)

    @staticmethod
    def __cond_add_param(
        params: Dict[str, Any],
        value: Optional[Any],
        key: str,
    ) -> Dict[str, Any]:
        """
        Helps with the building of the params for requests. A parameter will
        be added with a given key to the dict if the value is not `None`.
        Additionally if the value is a list it will be converted into a
        comma separated string.
        """
        if value is None:
            return params
        if isinstance(value, list):
            value = ",".join(value)
        params[key] = value
        return params

    def __build_return(
        self,
        response: requests.Response,
        as_dict: bool,
    ) -> Union[List[Dict], List[T]]:
        """
        Handles the return of fetched records. This is needed as some
        methods provide an option to return the result as a List of dicts
        rather a `BaseModel` derived model.
        """
        if self._type() is None:
            return response.json()

        rsl = []
        for item in response.json():
            tmp = self._type().parse_obj(item)
            if as_dict:
                rsl.append(tmp.dict())
            else:
                rsl.append(tmp)
        return rsl

    @staticmethod
    def __json_converter(value):
        if isinstance(value, datetime.date):
            return str(value)


def build_url(*args: Tuple[str]) -> str:
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
