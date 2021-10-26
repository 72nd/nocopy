# nocopy

Very simple REST client library for the Airtable alternative [NocoDB](https://nocodb.com/) with the optional ability of using [pydanitc](https://pydantic-docs.helpmanual.io/) models.

This by far not a complete implementation of the API. The project is the direct result of my needs for managing a project which uses NocoDB. The current state can be seen in the [todo](todo.md) document. You're welcome to extend and enhance this library.


## CLI App

There is an command line application using this

nocopy is first and foremost a library but it also provides a simple CLI for recurring tasks like in- and exporting data. Please note that in contrast to the library there are no type-checks nor any validation. So it's up to you to check your input data.


## Usage

For this section we assume the following Noco table (which contains some school lessons):

```json
{
	"id": "int",
	"title": "string",
	"created_at": "string",
	"updated_at": "string",
	"date": "string",
	"time": "string"
}
```

### Instantiate a client using pydantic model

You can use [pydantic](https://pydantic-docs.helpmanual.io/) to define the structure of your NocoDB table as a model. This provides you with additional niceties provided by pydantic like validation. If possible it's highly recommended to use this feature.


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

As you see Generics are used to tie a `Client` instance to a specific pydantic `BaseModel`. Please note the following:

_Remark 1:_ Your model needs a `id` field.  
_Remark 2:_ As you see Noco uses strings for dates and times. As it uses the default date-format you can use pydantic to simplicity convert them into the respective python types.


### Instantiate generic client

It's not always possible to know the structure of the NocoDB table in advance and thus being able to define concrete pydantic model for it (like when writing a application for interacting with arbitrary NocoDB databases). That's why nocopy also supports the interaction with the database using dictionaries as a generic data structure. This is simply archived by not defining a BaseModel as below:

```python
form nocopy import Client

# Instantiate a generic Client instance.
generic_client = Client(
	"https://noco.example.com/nc/project/api/v1/lessons",
	"SECRET_AUTH_TOKEN",
)
``` 


### Add record(s)

Add a new record using the pydantic model `Lesson`.

```python
client.add(Lesson(
	title="Math",
	date=datetime.time(2021, 2, 3),
	time=datetime.time(10, 0),
))
``` 

Add multiple records at once using a list of model instances.

```python
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

Add (a) record(s) using the generic client.

```python
generic_client.add(dict{
	"title": "Math",
	"date": datetime.time(2021, 2, 3),
	"time": datetime.time(10, 0),
})
generic_client.add([
	{
		"title": "Math",
		"date": datetime.time(2021, 2, 3),
		"time": datetime.time(10, 0),
	},
	{
		"title": "English",
		"date": datetime.time(2021, 2, 3),
		"time": datetime.time(10, 0),
	},
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
