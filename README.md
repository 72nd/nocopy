# nocopy

Very simple REST client for the Airtable alternative [NocoDB](https://nocodb.com/) using [pydanitc](https://pydantic-docs.helpmanual.io/) models.

(This by far not a complete implementation of the API, it's what I need for the moment.)


## Example/Methods

Example for the Noco table (which contains some school lessons) with the following model:

```json
{
  "id": int,
  "title": "string",
  "created_at": "string",
  "updated_at": "string",
  "date": "string",
  "time": "string"
}
```

_Remark 1:_ Your model should have a `id` field.  
_Remark 2:_ As you see Noco uses strings for dates and times. As it uses the default date-format you can use pydantic to simplicity convert them into the respective python types.

```python
from pydantic import BaseModel
form nocopy import Client

import datetime

class Lesson(BaseModel):
	"""Defines the Lesson model."""
	id: int
	title: str
	created_at: datetime.datetime
	updated_at: datetime.datetime
	date: datetime.date
	time: datetime.time

# Build client for the specific model.
client = Client[Lesson](
	"https://noco.example.com/nc/project/api/v1/lessons",
	"SECRET_AUTH_TOKEN",
)
``` 


### Add record(s)

```python
# Add a new record.
client.add(Lesson(
	title="Math",
	date=datetime.time(2021, 2, 3),
	time=datetime.time(10, 0),
))

# Add multiple records at once (bulk).
client.add([
	Lesson(
		title="Math",
		date=datetime.time(2021, 2, 3),
		time=datetime.time(10, 0),
	),
	Lesson(
		title="English",
		date=datetime.time(2021, 2, 3),
		time=datetime.time(12, 0),
	),
])
``` 


### List

You can make more fancy queries using NocoDB's [query params](https://docs.nocodb.com/developer-resources/rest-apis#query-params). Available kwargs: `where, limit, offset, sort, fields, fields1`. More about the usage in the documentation of NocoDB.

```python
>>> client.list(where="(title,eq,Math)")
[Lesson(id=0, title="Math", ...)]
```


### Get by id

```python
>>> client.by_id(0)
[Lesson(id=0, title="Math", ...)]
```


### Update record

A record can by updated by giving it's `id` and a dict mapping the desired field name to the new value (will just update the selected field) or a model (exchanging the whole record).

```python
# Using a new model.
client.update(0, Lesson(
	title="French",
	date=datetime.time(2021, 4, 2),
	time=datetime.time(14, 0),
))

# Selective updating using a dict.
client.update(0, {"title": "Biology"})
```


### Delete

You can delete a record by providing it's `id`:

```python
client.delete(0)
```
