from abc import ABC, abstractmethod
from enum import Enum
from json import dumps
from typing import Dict, List, cast
from uuid import UUID
from varname import nameof

from cbltest.logging import cbl_warning
from cbltest.requests import TestServerRequest, TestServerRequestBody
from cbltest.assertions import _assert_not_null

# Some conventions that are followed in this file are that all request classes that
# will be sent to the test server are classes that end in 'Request'.  Their bodies
# are the same class name, except with 'Body' appended.  For example, PostResetRequest
# will accept PostResetRequestBody.  The type is generic in the constructor in order
# to facilitate easy API versioning, but an assert will check the type is correct.

# All other classes support the RequestBody classes

class PostResetRequestBody(TestServerRequestBody):
    """
    The body of a POST /reset request as specified in version 1 of the 
    `spec <https://github.com/couchbaselabs/couchbase-lite-tests/blob/main/spec/api/api.yaml>`_

    Example Body::

        {
            "datasets": {
                "catalog": [
                    "db1",
                    "db2"
                ]
            }
        }
    """

    @property
    def datasets(self) -> Dict[str, List[str]]:
        """
        Gets the datasets contained in the :class:`PostResetRequestBody`
        """
        return self.__datasets
    
    def __init__(self):
        super().__init__(1)
        self.__datasets = {}

    def add_dataset(self, name: str, result_db_names: List[str]) -> None:
        """
        Add a dataset entry to the :class:`PostResetRequestBody`

        :param name: The name of the dataset to add (i.e. catalog in the class docs example)
        :param result_db_names: A list of databases to populate with the data from the dataset
        """
        self.__datasets[name] = result_db_names

    def serialize(self) -> str:
        """
        Serializes the :class:`PostResetRequestBody` to a JSON string
        """
        return f'{{"datasets": {dumps(self.__datasets)}}}'
    
class PostGetAllDocumentIDsRequestBody(TestServerRequestBody):
    """
    The body of a POST /getAllDocumentIDs request as specified in version 1 of the 
    `spec <https://github.com/couchbaselabs/couchbase-lite-tests/blob/main/spec/api/api.yaml>`_

    Example Body::

        {
            "database": "db1",
            "collections": [
                "catalog.cloths",
                "catalog.shoes"
            ]
        }
    """

    @property
    def collections(self) -> List[str]:
        """
        Gets the collections specified in the :class:`PostGetAllDocumentIDsRequestBody`
        """
        return self.__collections
    
    def __init__(self, database: str = None, collections: List[str] = None):
        super().__init__(1)
        self.database = database
        """The database to get document IDs from"""

        self.__collections = collections if collections is not None else []

    def serialize(self) -> str:
        """
        Serializes the :class:`PostGetAllDocumentIDsRequestBody` to a JSON string
        """
        raw = {"database": self.database, "collections": self.__collections}
        return dumps(raw)
    
class DatabaseUpdateType(Enum):
    """
    An enum specifying a type of database update to perform
    """

    UPDATE = "UPDATE"
    """Modifies the content of a given document"""

    DELETE = "DELETE"
    """Deletes a given document using the deletion API"""

    PURGE = "PURGE"
    """Purges a given document using the purge API"""

    def __str__(self) -> str:
        return self.value
    
class DatabaseUpdateEntry:
    """
    A class representing a single update to perform on a database.  These entries
    can be passed via :class:`PostUpdateDatabaseRequestBody` to perform batch operations
    """
    
    def __init__(self, type: DatabaseUpdateType, collection: str, document_id: str,
                 updated_properties: Dict[str, any] = None, removed_properties: Dict[str, any] = None) -> None:
        self.type: DatabaseUpdateEntry = cast(DatabaseUpdateEntry, _assert_not_null(type, nameof(type)))
        """The type of update to be performed"""

        self.collection: str = cast(str, _assert_not_null(collection, nameof(collection)))
        """The collection to that the document to be modified belongs to"""

        self.document_id: str = cast(str, _assert_not_null(document_id, nameof(document_id)))
        """The ID of the document to be modified"""

        self.updated_properties: Dict[str, any] = updated_properties
        """
        The properties to be updated on a given document. 
        Note that to remove a property, `removed_properties` must be used.
        The values of the dictionary entries should simply be null.
        It has no meaning if `type` is not `UPDATE`
        """

        self.removed_properties: Dict[str, any] = removed_properties
        """
        The properties to be removed on a given document. 
        The values of the dictionary entries should simply be null.
        It has no meaning if `type` is not `UPDATE`
        """

    def is_valid(self) -> bool:
        """
        Returns `True` if this update is valid, or `False` if it is not.  An update is
        considered valid if it is a PURGE / DELETE, or if it is an UPDATE with at least
        one updated or one removed property
        """
        if self.type != DatabaseUpdateType.UPDATE:
            return True
        
        return len(self.__updated_properties) > 0 or len(self.__removed_properties) > 0
    
    def to_dict(self) -> Dict[str, any]:
        """
        Transforms the :class:`DatabaseUpdateEntry` into a serialized dictionary object
        """
        if not self.is_valid():
            return None
        
        raw = {
            "type": str(self.type),
            "collection": self.collection,
            "documentID": self.document_id
        }

        if self.type != DatabaseUpdateType.UPDATE:
            return raw

        if self.updated_properties is not None and len(self.updated_properties) > 0:
            raw["updatedProperties"] = self.updated_properties

        if self.removed_properties is not None and len(self.removed_properties) > 0:
            raw["removedProperties"] = self.removed_properties

        return raw
    
class PostUpdateDatabaseRequestBody(TestServerRequestBody):
    """
    The body of a POST /updateDatabase request as specified in version 1 of the 
    `spec <https://github.com/couchbaselabs/couchbase-lite-tests/blob/main/spec/api/api.yaml>`_

    Example Body::

        {
            "database": "db1",
            "updates": [
                {
                    "type": "UPDATE",
                    "collection": "store.cloths",
                    "documentID": "doc1",
                    "updatedProperties": {
                        "name": "Cool Sport Tech Fleece Shirt"
                    },
                    "removedProperties": {
                        "vendor": {
                        "info": null
                        }
                    }
                }
            ]
        }
    """
    
    def __init__(self, database: str = None, updates: List[DatabaseUpdateEntry] = None):
        super().__init__(1)
        self.database: str = database
        """The database that the updates will be applied to once executed"""

        self.updates: List[DatabaseUpdateEntry] = updates
        """
        The list of updates on the :class:`PostUpdateDatabaseRequestBody`.
        This list can be directly added to or removed from.
        """

    def serialize(self) -> str:
        """Serializes the :class:`PostUpdateDatabaseRequestBody` to a JSON string"""

        raw = {
            "database": self.database
        }

        raw_entries = []

        for e in self.updates:
            raw_entry = e.to_dict()
            if raw_entry is None:
                cbl_warning("Skipping invalid DatabaseUpdateEntry in body serialization!")
                continue

            raw_entries.append(raw_entry)

        raw["updates"] = raw_entries
        return dumps(raw)
    
class SnapshotDocumentEntry:
    """
    A class for recording the fully qualified name of a document to be saved in a snapshot.
    This class is used in conjunction with :class:`PostSnapshotDocumentsRequestBody`
    """
    def __init__(self, collection: str, id: str):
        self.collection: str = collection
        """The collection that the snapshotted document belongs to"""

        self.id: str = id
        """The ID of the snapshotted document"""

    def to_dict(self) -> Dict[str, any]:
        """
        Transforms the :class:`SnapshotDocumentEntry` into a serialized dictionary object
        """
        return {"collection": self.collection, "id": self.id}
    
class PostSnapshotDocumentsRequestBody(TestServerRequestBody):
    """
    The body of a POST /snapshotDocuments request as specified in version 1 of the 
    `spec <https://github.com/couchbaselabs/couchbase-lite-tests/blob/main/spec/api/api.yaml>`_

    Example Body::

        [
            {
                "collection": "store.cloths",
                "id": "doc1"
            }
        ]
    """

    def entries(self) -> List[SnapshotDocumentEntry]:
        """
        Gets the (mutable) list of documents to be snapshotted.  This list can be
        directly added to or removed from
        """
        return self.__entries
    
    def __init__(self, entries: List[SnapshotDocumentEntry] = None):
        super().__init__(1)
        self.__entries = entries if entries is not None else []

    def serialize(self) -> str:
        """Serializes the :class:`PostSnapshotDocumentsRequestBody` to a JSON string"""
        raw = [e.to_dict() for e in self.entries] if self.entries is not None else []
        return dumps(raw)

class PostVerifyDocumentsRequestBody(TestServerRequestBody):
    """
    The body of a POST /verifyDocuments request as specified in version 1 of the 
    `spec <https://github.com/couchbaselabs/couchbase-lite-tests/blob/main/spec/api/api.yaml>`_

    Example Body::

        {
            "database": "db1",
            "snapshot": "123e0000-e89b-12d3-a456-426614174000",
            "changes": [
                {
                    "type": "UPDATE",
                    "collection": "store.cloths",
                    "documentID": "doc1",
                    "updatedProperties": {
                        "name": "Cool Sport Tech Fleece Shirt"
                    },
                    "removedProperties": {
                        "vendor": {
                        "info": null
                        }
                    }
                }
            ]
        }
    """

    @property
    def snapshot(self) -> str:
        """Gets the snapshot used as a baseline for the comparison"""
        return self.__snapshot
    
    @property
    def database(self) -> str:
        """Gets the database that will be used to retrieve the current state"""
        return self.__database
    
    def __init__(self, database: str, snapshot: str, changes: List[DatabaseUpdateEntry] = None):
        super().__init__(1)
        self.__snapshot = snapshot
        self.__database = database
        self.changes = changes
        """A list of changes to verify in the database (as compared to the `snapshot`)"""

    def serialize(self) -> str:
        """Serializes the :class:`PostVerifyDocumentsRequestBody` to a JSON string"""
        raw = {
            "snapshot": self.__snapshot,
            "database": self.__database,
            "changes": [c.to_dict() for c in self.changes] if self.changes is not None else []
        }

        return dumps(raw)
    
class ReplicatorType(Enum):
    """An enum representing the direction of a replication"""

    PUSH = "push"
    """Local to remote only"""

    PULL = "pull"
    """Remote to local only"""

    PUSH_AND_PULL = "pushAndPull"
    """Bidirectional"""

    def __str__(self) -> str:
        return self.value
    
class ReplicatorAuthenticator(ABC):
    """
    The base class for replicator authenticators
    """

    @property
    def type(self) -> str:
        """Gets the type of authenticator (required for all authenticators)"""
        return self.__type

    def __init__(self, type: str) -> None:
        self.__type = type

    @abstractmethod
    def to_dict(self) -> Dict[str, any]:
        return None
    
class ReplicatorBasicAuthenticator(ReplicatorAuthenticator):
    """A class holding information to perform HTTP Basic authentication"""

    @property
    def username(self) -> str:
        """Gets the username that will be used for auth"""
        return self.__username
    
    def password(self) -> str:
        """Gets the password that will be used for auth"""
        return self.__password
    
    def __init__(self, username: str, password: str) -> None:
        super().__init__("basic")
        self.__username = username
        self.__password = password

    def to_dict(self) -> Dict[str, any]:
        """Transforms the :class:`ReplicatorBasicAuthenticator` into a JSON dictionary"""
        return {
            "type": "basic",
            "username": self.__username,
            "password": self.__password
        }
    
class ReplicatorSessionAuthenticator(ReplicatorAuthenticator):
    """A class holding information to authenticate via session cookie"""

    @property 
    def session_id(self) -> str:
        """Gets the session ID that will be used for auth"""
        return self.__session_id
    
    @property
    def cookie_name(self) -> str:
        """Gets the cookie name that will be used for auth"""
        return self.__cookie_name
    
    def __init__(self, session_id: str, cookie_name: str = "SyncGatewaySession") -> None:
        super().__init__("session")
        self.__session_id = session_id
        self.__cookie_name = cookie_name

    def to_dict(self) -> Dict[str, any]:
        """Transforms the :class:`ReplicatorSessionAuthenticator` into a JSON dictionary"""
        return {
            "type": "session",
            "sessionID": self.__session_id,
            "cookieName": self.__cookie_name
        }
    
class ReplicatorPushFilterParameters:
    """
    A class representing parameters to be passed to a push filter.
    In theory this could be anything, but in practice it has always been
    just documentIDs.
    """

    def __init__(self) -> None:
        self.document_ids: List[str] = None
        """The document IDs to filter, if any"""

    def to_dict(self) -> Dict[str, any]:
        """Transforms the :class:`ReplicatorPushFilterParameters` into a JSON dictionary"""
        if self.document_ids is None:
            return None
        
        return {
            "documentIDs": self.document_ids
        }
    
class ReplicatorPushFilter:
    """
    A class representing a push filter to use on a replication to limit
    the documents that get sent from local to remote.
    """

    @property
    def name(self) -> str:
        """Gets the name of the push filter"""
        return self.__name
    
    def __init__(self, name: str):
        self.__name = name
        self.parameters = cast(ReplicatorPushFilterParameters, None)
        """The parameters to be applied to the push filter"""

    def to_dict(self) -> Dict[str, any]:
        """Transforms the :class:`ReplicatorPushFilter` into a JSON dictionary"""
        ret_val = {"name": self.name}
        if self.parameters is not None:
            ret_val["params"] = self.parameters.to_dict()

class ReplicatorCollectionEntry:
    """
    A class representing configuration for a collection in a given replication
    """
    @property
    def collection(self) -> str:
        """Gets the name of the collection the configuration applies to"""
        return self.__collection
    
    def __init__(self, collection: str):
        self.__collection = collection
        self.channels: List[str] = []
        """A list of channels to use when replicating"""

        self.document_ids: List[str] = []
        """A list of document IDs to replicate.  All other documents will be ignored."""

        self.push_filter: ReplicatorPushFilter = None
        """A filter to apply to the replication.  Failing documents will be rejected."""
    
class PostStartReplicatorRequestBody(TestServerRequestBody):
    """
    The body of a POST /startReplicator request as specified in version 1 of the 
    `spec <https://github.com/couchbaselabs/couchbase-lite-tests/blob/main/spec/api/api.yaml>`_

    Example Body::

        {
            "config": {
                "database": "db1",
                "collections": [
                {
                    "collection": "store.cloths",
                    "channels": [
                        "A",
                        "B"
                    ],
                    "documentIDs": [
                        "doc1",
                        "doc2"
                    ],
                    "pushFilter": {
                        "name": "documentIDs",
                        "params": {
                            "documentIDs": [
                            "doc1",
                            "doc2"
                            ]
                        }
                    }
                }
                ],
                "endpoint": "wss://localhost:4985/db",
                "replicatorType": "pushAndPull",
                "continuous": true,
                "authenticator": {
                "type": "BASIC",
                "username": "user1",
                "password": "p@ssw0rd"
                }
            },
            "reset": false
        }
    """

    @property
    def database(self) -> str:
        """Gets the local database that this replicator will be created for"""
        return self.__database
    
    @property
    def endpoint(self) -> str:
        """Gets the remote URL endpoint that this replicator will replicate to"""
        return self.__endpoint

    def __init__(self, database: str, endpoint: str):
        super().__init__(1)
        self.__database = database
        self.__endpoint = endpoint
        self.replicatorType: ReplicatorType = ReplicatorType.PUSH_AND_PULL
        """The direction to be performed during the replication"""

        self.continuous: bool = False
        """Whether or not this is a continuous replication (i.e. doesn't stop when finished
        with its initial changes)"""

        self.authenticator: ReplicatorAuthenticator = None
        """The authenticator to use to perform authentication with the remote"""

        self.reset: bool = False
        """Whether or not to start the replication over from the beginning"""

        self.collections: List[ReplicatorCollectionEntry] = None
        """The per-collection configuration to use inside the replication"""

    def serialize(self) -> str:
        """Serializes the :class:`PostStartReplicatorRequestBody` to a JSON string"""
        raw = {
            "database": self.__database,
            "endpoint": self.__endpoint,
            "replicatorType": str(self.replicatorType),
            "continuous": self.continuous,
            "reset": self.reset
        }

        if self.collections is not None:
            raw["collections"] = [c.to_dict() for c in self.collections]

        if self.authenticator is not None:
            raw["authenticator"] = self.authenticator.to_dict()

        return dumps(raw)
    
class PostGetReplicatorStatusRequestBody(TestServerRequestBody):
    """
    The body of a POST /getReplicatorStatus request as specified in version 1 of the 
    `spec <https://github.com/couchbaselabs/couchbase-lite-tests/blob/main/spec/api/api.yaml>`_

    Example Body::

        {
            "id": "123e4567-e89b-12d3-a456-426614174000"
        }
    """

    @property
    def id(self) -> str:
        """Gets the ID of the replicator to check the status for"""
        return self.__id
    
    def __init__(self, id: str):
        super().__init__(1)
        self.__id = id

    def serialize(self) -> str:
        """Serializes the :class:`PostGetReplicatorStatusRequestBody` to a JSON string"""
        return {"id": self.__id}
    

# Below this point are all of the concrete test server request types
# Remember the note from the top of this file about the actual type of the payload
class PostResetRequest(TestServerRequest):
    """
    A POST /reset request as specified in version 1 of the 
    `spec <https://github.com/couchbaselabs/couchbase-lite-tests/blob/main/spec/api/api.yaml>`_
    """
    def __init__(self, uuid: UUID, payload: TestServerRequestBody):
        super().__init__(1, uuid, "reset", PostResetRequestBody, payload=payload)

class PostGetAllDocumentIDsRequest(TestServerRequest):
    """
    A POST /getAllDocumentIDs request as specified in version 1 of the 
    `spec <https://github.com/couchbaselabs/couchbase-lite-tests/blob/main/spec/api/api.yaml>`_
    """
    def __init__(self, uuid: UUID, payload: TestServerRequestBody):
        super().__init__(1, uuid, "getAllDocumentIDs", PostGetAllDocumentIDsRequestBody, payload=payload)

class PostUpdateDatabaseRequest(TestServerRequest):
    """
    A POST /updateDatabase request as specified in version 1 of the 
    `spec <https://github.com/couchbaselabs/couchbase-lite-tests/blob/main/spec/api/api.yaml>`_
    """
    def __init__(self, uuid: UUID, payload: TestServerRequestBody):
        super().__init__(1, uuid, "updateDatabase", PostUpdateDatabaseRequestBody, payload=payload)

class PostSnapshotDocumentsRequest(TestServerRequest):
    """
    A POST /snapshotDocuments request as specified in version 1 of the 
    `spec <https://github.com/couchbaselabs/couchbase-lite-tests/blob/main/spec/api/api.yaml>`_
    """
    def __init__(self, uuid: UUID, payload: TestServerRequestBody):
        super().__init__(1, uuid, "snapshotDocuments", PostSnapshotDocumentsRequestBody, payload=payload)
    
class PostVerifyDocumentsRequest(TestServerRequest):
    """
    A POST /verifyDocuments request as specified in version 1 of the 
    `spec <https://github.com/couchbaselabs/couchbase-lite-tests/blob/main/spec/api/api.yaml>`_
    """
    def __init__(self, uuid: UUID, payload: TestServerRequestBody):
        super().__init__(1, uuid, "verifyDocuments", PostVerifyDocumentsRequestBody, payload=payload)

class PostStartReplicatorRequest(TestServerRequest):
    """
    A POST /startReplicator request as specified in version 1 of the 
    `spec <https://github.com/couchbaselabs/couchbase-lite-tests/blob/main/spec/api/api.yaml>`_
    """
    def __init__(self, uuid: UUID, payload: TestServerRequestBody):
        super().__init__(1, uuid, "startReplicator", PostStartReplicatorRequestBody, payload=payload)

class PostGetReplicatorStatusRequest(TestServerRequest):
    """
    A POST /getReplicatorStatus request as specified in version 1 of the 
    `spec <https://github.com/couchbaselabs/couchbase-lite-tests/blob/main/spec/api/api.yaml>`_
    """
    def __init__(self, uuid: UUID, payload: TestServerRequestBody):
        super().__init__(1, uuid, "getReplicatorStatus", PostGetReplicatorStatusRequestBody, payload=payload)