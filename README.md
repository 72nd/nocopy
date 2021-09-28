# nocopy

Very simple REST client library and CLI app for the Airtable alternative [NocoDB](https://nocodb.com/) using [pydanitc](https://pydantic-docs.helpmanual.io/) models.

(This by far not a complete implementation of the API, it's what I need for the moment. Current progress [here](todo.md))


## CLI Usage

nocopy is first and foremost a library but it also provides a simple CLI for recurring tasks like in- and exporting data. Please note that in contrast to the library there are no type-checks nor any validation. So it's up to you to check your input data.


### Configuration

The application has to know the URL and the secret token of your API endpoint. There are three different possibilities to define them:

1. Using the `-u/--url` and `-k/--token` flags.
2. Setting the `NOCO_URL` and `NOCO_TOKEN` environment variable.
3. Using a configuration file.

The configuration file is a simple JSON file. Which can be generated using the CLI:

```shell script
nocopy init -o config.json
```


### A word on in/output files and their formats

A number of nocopy-cli's operation consist of reading or writing from/to a file. Currently [YAML](https://en.wikipedia.org/wiki/YAML), [CSV](https://en.wikipedia.org/wiki/Comma-separated_values) and [JSON](https://en.wikipedia.org/wiki/JSON) are supported ether as file or per stdin/stdout. The application tries to determine the format based on the file extension. Otherwise YAML will be used. Use the `-f/--format` flag to specify the format.


### Pull

Pull/download the records from the NocoDB into a CSV file. The first row will contain the name of the columns.

```shell script
nocopy pull -c config.json -t Lessons -o exported-lessons.csv
```

Optionally the [NocoDB's query parameters](https://docs.nocodb.com/developer-resources/rest-apis#query-params) are supported:

- `--where` Complicated where conditions.
- `--limit` Number of rows to get(SQL limit value).
- `--offset` Offset for pagination(SQL offset value).
- `--sort` Sort by column name, Use `-` as prefix for descending sort.
- `--fields` Required column names in result.
- `--fields1` Required column names in child result.


### Push

You can push/upload the content of a CSV file to the NocoDB (remember: there is no data validation whatsoever). The first row has to contain the names of the columns as in the NocoDB model. You can use the `template` command (see below) to obtain an empty CSV file with the correct header row. 

```shell script
nocopy push -c config.json -t Lessons -i raw-lessons.csv
```

Empty cells are parsed as `None`. For Boolean values (`True` and `False`) use `True` and `False`.


### Init configuration

Just a small convince function. Generates a new config file.

```shell script
nocopy init -o config.json
```


### Purge

Deletes all records of a table as there is no native function for that in NocoDB (yet). Most of the time a rater stupid idea, takes also a considerable amount of time when running.

```shell script
nocopy purge -c config.json -t Lessons
```


### Update

You can update records in the NocoDB. The id has to be specified in the CSV.

```shell script
nocopy update -c config.json -t Lessons -i update-lessons.csv
```

### CSV Template

Generates an empty CSV file with the correct header row. (Table on the NocoDB server has to contain at least one record for this to work.)

```shell script
nocopy template -c config.json -t Lessons -o lessons-template.csv
```


## Library example

Example for the Noco table (which contains some school lessons) with the following model:

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
