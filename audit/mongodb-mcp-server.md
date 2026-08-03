# MCP audit - `node audit/node_modules/mongodb-mcp-server/dist/esm/index.js`

**Score: 100/100 (grade A)** · 29 tools · 0 fail / 0 warn / 28 info / 263 ok

| Tool | Check | Severity | Detail |
|---|---|---|---|
| `aggregate-db` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `aggregate` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `collection-indexes` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `collection-schema` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `collection-storage-size` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `connect` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `count` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `create-collection` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `create-index` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `db-stats` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `delete-many` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `drop-collection` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `drop-database` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `drop-index` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `explain` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `export` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `find` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `insert-many` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `list-collections` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `list-databases` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `mongodb-logs` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `rename-collection` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `update-many` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `atlas-local-connect-deployment` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `atlas-local-create-deployment` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `atlas-local-delete-deployment` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `atlas-local-list-deployments` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `search-knowledge` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |

## Tools discovered

- **`aggregate-db`** - Run an aggregation against a MongoDB database (3 params, 2 required)
- **`aggregate`** - Run an aggregation against a MongoDB collection (4 params, 3 required)
- **`collection-indexes`** - Describe the indexes for a collection (2 params, 2 required)
- **`collection-schema`** - Describe the schema for a collection (4 params, 2 required)
- **`collection-storage-size`** - Gets the size of the collection (2 params, 2 required)
- **`connect`** - Connect to a MongoDB instance. The config resource captures if the server is already connected to a MongoDB cluster. If the user has configured a connection string or has previously called the connect tool, a connection is already established and there's no need to call this tool unless the user has explicitly requested to switch to a new MongoDB cluster. (1 params, 1 required)
- **`count`** - Gets the number of documents in a MongoDB collection using db.collection.count() and query as an optional filter parameter (3 params, 2 required)
- **`create-collection`** - Creates a new collection in a database. If the database doesn't exist, it will be created automatically. (2 params, 2 required)
- **`create-index`** - Create an index for a collection (4 params, 3 required)
- **`db-stats`** - Returns statistics that reflect the use state of a single database (1 params, 1 required)
- **`delete-many`** - Removes all documents that match the filter from a MongoDB collection (3 params, 2 required)
- **`drop-collection`** - Removes a collection or view from the database. The method also removes any indexes associated with the dropped collection. (2 params, 2 required)
- **`drop-database`** - Removes the specified database, deleting the associated data files (1 params, 1 required)
- **`drop-index`** - Drop an index for the provided database and collection. (4 params, 4 required)
- **`explain`** - Returns statistics describing the execution of the winning plan chosen by the query optimizer for the evaluated method (4 params, 3 required)
- **`export`** - Export a query or aggregation results in the specified EJSON format. (5 params, 4 required)
- **`find`** - Run a find query against a MongoDB collection (7 params, 2 required)
- **`insert-many`** - Insert an array of documents into a MongoDB collection. If the list of documents is above com.mongodb/maxRequestPayloadBytes, consider inserting them in batches. (3 params, 3 required)
- **`list-collections`** - List all collections for a given database (1 params, 1 required)
- **`list-databases`** - List all databases for a MongoDB connection (0 params, 0 required)
- **`mongodb-logs`** - Returns the most recent logged mongod events (2 params, 0 required)
- **`rename-collection`** - Renames a collection in a MongoDB database (4 params, 3 required)
- **`update-many`** - Updates all documents that match the specified filter for a collection. If the list of documents is above com.mongodb/maxRequestPayloadBytes, consider updating them in batches. (5 params, 3 required)
- **`atlas-local-connect-deployment`** - Connect to a MongoDB Atlas Local deployment (1 params, 1 required)
- **`atlas-local-create-deployment`** - Create a MongoDB Atlas local deployment. Default image is preview. When the user does not specify an image tag, inform them that preview is used by default and provide this link for more information: https://hub.docker.com/r/mongodb/mongodb-atlas-local (3 params, 0 required)
- **`atlas-local-delete-deployment`** - Delete a MongoDB Atlas local deployment (1 params, 1 required)
- **`atlas-local-list-deployments`** - List MongoDB Atlas local deployments (0 params, 0 required)
- **`list-knowledge-sources`** - List available data sources in the MongoDB Assistant knowledge base. Use this to explore available data sources or to find search filter parameters to use in search-knowledge. (0 params, 0 required)
- **`search-knowledge`** - Search for information in the MongoDB Assistant knowledge base. This includes official documentation, curated expert guidance, and other resources provided by MongoDB. Supports filtering by data source and version. (3 params, 1 required)

---
_Generated by [mcp-probe](https://github.com/junaidshahid-dev/mcp-probe)._