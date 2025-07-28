# Copyright (c) 2023-2024-2025 Codelet Team (pyxfluff / iiPythonx)

# Modules
from AOS import globals
from AOS.deps import il

from typing import Any, List, Dict

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure


# Main database class
class Database(object):
    def __init__(self) -> None:
        dbattrs = globals.dbattrs

        for db_item in [
            "apps",
            "logs",
            "places",
            "secrets",
            "v2_logs",
            "api_keys",
            "sessions",
            "bot_store",
            "abuse_logs",
            "error_refs",
            "reported_versions",
            "discord_remote_secrets"
        ]:
            setattr(self, db_item.upper(), db_item)

        client = MongoClient(
            dbattrs["address"],
            serverSelectionTimeoutMS=dbattrs["timeout_ms"],
            **(
                {
                    "username": dbattrs["auth"]["username"],
                    "password": dbattrs["auth"]["password"]
                }
                if dbattrs["auth"]["use_auth"]
                else {}
            )
        )

        self.db = client[dbattrs["use_prod_db"] and "administer" or "administer_dev"]

        try:
            client.admin.command("ping")

        except ConnectionFailure as e:
            print(
                "Failed to connect to MongoDB within the required timeframe! Is Mongo running? Aborting startup..."
            )
            raise e

        server_info = client.server_info()
        repl_status = client.admin.command("replSetGetStatus")

        if repl_status:
            me = next(
                (
                    m
                    for m in repl_status["members"]
                    if m.get("name") == dbattrs["address"].replace("mongodb://", "")
                ),
                None
            )

            replica_state = me["stateStr"] if me else "UNKNOWN"
        else:
            replica_state = "STANDALONE"

        il.cprint(
            f"[✓] Connected to MongoDB {server_info["version"]} {server_info["gitVersion"][:7]} at {dbattrs['address']}:/{dbattrs["use_prod_db"] and 'administer' or 'administer_dev'} <RCN [{replica_state} {repl_status["set"]}]>",
            32
        )

    def set(self, key: str | int, value: Any, db: str) -> None:
        assert isinstance(key, (str, int)), "key must be a string (integers accepted)!"
        assert isinstance(db, str), "db must be a string!"

        if db == self.APPS:
            key = str(key)

        db = self.db[db]

        internal_document = {"administer_id": str(key)}
        active_document = db.find_one(internal_document)
        if active_document is not None:
            return db.update_one(
                {"_id": active_document["_id"]}, {"$set": {"data": value}}
            )

        return db.insert_one(internal_document | {"data": value})

    def set_batch(self, items: Dict[str | int, dict], db: str) -> None:
        assert isinstance(items, dict), "items must be a dict!"
        assert isinstance(db, str), "db must be a string!"

        for k, v in items.items():
            self.set(k, v, db)

    def get(self, key: str | int, db: str) -> dict | None:
        assert isinstance(key, (str, int)), "key must be a string (integers accepted)"
        assert isinstance(db, str), "db must be an attr of db"

        document = self.db[db].find_one({"administer_id": str(key)})
        return document and document["data"]

    def find(self, identifier: dict, db: str) -> str | None:
        assert isinstance(identifier, dict), "identifier must be a dict!"
        assert isinstance(db, str), "db must be a string!"

        document = self.db[db].find_one({f"data.{k}": v for k, v in identifier.items()})
        return document and document["administer_id"]

    def delete(self, key: str | int, db: str) -> None:
        assert isinstance(key, (str, int)), "key must be a string or integer!"

        self.db[db].delete_one({"administer_id": str(key)})

    def bulk_delete(self, keys: List[str | int], db: str) -> None:
        assert isinstance(keys, list), "keys must be a list! (try using db.delete())"

        self.db[db].delete_many({"administer_id": {"$in": keys}})

    def get_all(self, db: str) -> dict:
        return list(self.db[db].find())

    def get_all_paged(self, db: str, limit: int, page: int) -> List[dict]:
        return [
            d["data"]
            for d in list(
                self.db[db].aggregate(
                    [{"$skip": limit * (page - 1)}, {"$limit": limit}]
                )
            )
        ]

    # Wrappers for raw MongoDB operations
    def raw_insert(self, item: dict, db: str) -> None:
        self.db[db].insert_one(item)

    def raw_find(self, identifier: dict, db: str) -> dict:
        return self.db[db].find_one(identifier)

    def raw_del(self, identifier: dict, db: str) -> dict:
        return self.db[db].delete_one(identifier)

    def raw_purge(self, identifier: dict, db: str) -> dict:
        return self.db[db].delete_many(identifier)

    def raw_find_all(self, identifier: dict, db: str) -> List[dict]:
        return self.db[db].find(identifier)


# Initialize db
db = Database()

if globals.dbattrs["use_prod_db"]:
    il.cprint("[!] Production database is enabled. Proceed with caution!", 35)
