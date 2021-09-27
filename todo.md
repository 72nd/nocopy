# ToDo

Because why not.

## Basics

- [x] POST `/nc/{project}/api/v1/{table}` Add a new blocks
- [ ] GET `/nc/{project}/api/v1/{table}` Get list
	- [x] fields
	- [ ] bt, Comma separated parent table names(Belongs To)
	- [ ] hm, Comma separated child table names(Has Many)
	- [ ] mm, Comma separated child table names(Many to Many)
	- [x] where
	- [x] limit
	- [ ] limit: All when `None` given
	- [x] offset
	- [x] sort
- [ ] GET `/nc/{project}/api/v1/{table}/{id}` Get record by id
	- [x] id
	- [ ] bt, Comma separated parent table names(Belongs To)
	- [ ] hm, Comma separated child table names(Has Many)
	- [ ] mm, Comma separated child table names(Many to Many)
- [x] PUT `/nc/{project}/api/v1/{table}/{id}` Update a record
- [x] DELETE `/nc/{project}/api/v1/{table}/{id}` Delete a record
- [x] POST `/nc/{project}/api/v1/{table}/bulk` Bulk add a new records
- [ ] PUT `/nc/{project}/api/v1/{table}/{id}/bulk` Bulk update records
- [ ] DELETE `/nc/{project}/api/v1/{table}/{id}/bulk` Bulk delete records
- [ ] GET `/nc/{project}/api/v1/{table}/findOne` Get first from filtered data
	- [ ] fields
	- [ ] where
	- [ ] limit
	- [ ] offset
	- [ ] sort
- [ ] GET `/nc/{project}/api/v1/{table}/exists` Check record with provided id exists
- [ ] GET `/nc/{project}/api/v1/{table}/count` Count records
	- [ ] where
- [ ] GET `/nc/{project}/api/v1/{table}/groupby` Group by column
	- [ ] column_name
	- [ ] where
	- [ ] limit
	- [ ] offset
	- [ ] sort
- [ ] GET `/nc/{project}/api/v1/{table}/distribution` Calculate
	- [ ] column_name
	- [ ] min
	- [ ] max
	- [ ] step
	- [ ] steps
	- [ ] func, comma separated aggregation functions
- [ ] GET `/nc/{project}/api/v1/{table}/distinct` Get first one from filtered data
	- [ ] column_name
	- [ ] where
	- [ ] limit
	- [ ] offset
	- [ ] sort
- [ ] GET `/nc/{project}/api/v1/{table}/aggregate` Get first one from filtered data
	- [ ] column_name
	- [ ] func
	- [ ] having
	- [ ] fields
	- [ ] limit
	- [ ] offset
	- [ ] sort


## Relations

- [ ] How?
- [ ] Basic support
- [ ] Write ToDo
