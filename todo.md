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
	- [x] limit: All when `None` given
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
- [x] PUT `/nc/{project}/api/v1/{table}/{id}/bulk` Bulk update records
- [-] DELETE `/nc/{project}/api/v1/{table}/{id}/bulk` Bulk delete records
- [x] GET `/nc/{project}/api/v1/{table}/findOne` Get first from filtered data
	- [x] fields
	- [x] where
	- [x] limit
	- [x] offset
	- [x] sort
- [x] GET `/nc/{project}/api/v1/{table}/{id}/exists/` Check record with provided id exists
- [x] GET `/nc/{project}/api/v1/{table}/count` Count records
	- [x] where
- [x] GET `/nc/{project}/api/v1/{table}/groupby` Group by column
	- [x] column_name
	- [x] where
	- [x] limit
	- [x] offset
	- [x] sort
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
