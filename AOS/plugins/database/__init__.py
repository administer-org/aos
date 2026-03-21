# Copyright (c) 2023-2024-2025 Codelet Team (pyxfluff / iiPythonx)

# Modules
from AOS import globals, AOSError
from AOS.deps import il

from tqdm import tqdm
from time import time
from typing import Any, List, Dict

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Config
dbattrs = globals.dbattrs


# Main database class
class Database(object):
    def __init__(self, db_type) -> None:
        for db_item in [
            "apps",
            "logs",
            "places",
            "users",
            "secrets",
            "v2_logs",
            "sessions",
            "api_keys",
            "sessions",
            "bot_store",
            "abuse_logs",
            "error_refs",
            "signup_tokens",
            "reported_versions",
            "discord_remote_secrets"
        ]:
            setattr(self, db_item.upper(), db_item)

        def connect(address: str):
            # raise Exception("test")
            return MongoClient(
                address,
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

        try:
            if not dbattrs["addressv2"]["use_multiple_connections"]:
                client = connect(dbattrs["address"])
            elif dbattrs["addressv2"]["use_multiple_connections"]:
                with tqdm(dbattrs["addressv2"]["addresses"], desc="Testing optimal database to connect to") as bar:
                    databases = {}
                    for address in bar:
                        t = time()
                        client = connect(f"mongodb://{address}")

                        try:
                            client.admin.command("ping")
                        except ConnectionFailure:
                            tqdm.write(f"{address} is down!")
                            continue

                        elapsed_ms = (time() - t) * 1000

                        databases[address] = elapsed_ms
                        bar.set_description(f"Testing {address} (took {elapsed_ms:.2f}ms)")
                pick = min(databases.items(), key=lambda x: x[1])
                import logging
                logger = logging.getLogger(__name__)

                print(f"connecting to {pick[0]} (quickest @ {pick[1]}ms)")
                logger.info("connecting to %s (quickest @ %sms)", pick[0], pick[1])

                client = connect(f"mongodb://{pick[0]}")
                db_address = pick[0]
            else:
                raise AOSError(
                    "either AddressV2 or Address must be defined in the MongoConfig model"
                )

        except (
            KeyError,
            IndexError,
            TypeError
        ):  # support for not updated 5.6 config files
            client = connect(dbattrs["address"])
            db_address = dbattrs["address"].replace("mongodb://", "")

        self.db = client[db_type]

        try:
            client.admin.command("ping")

        except ConnectionFailure as e:
            print(
                "Failed to connect to MongoDB within the required timeframe! Is Mongo running? Aborting startup..."
            )
            logger.error("Failed to connect to MongoDB within the required timeframe")
            raise e

        server_info = client.server_info()

        try:
            repl_status = client.admin.command("replSetGetStatus")

            if repl_status:
                me = next(
                    (
                        m
                        for m in repl_status["members"]
                        if m.get("name") == db_address
                    ),
                    None
                )

                replica_state = me["stateStr"] if me else "UNKNOWN"
            else:
                replica_state = "STANDALONE"

            il.cprint(
                f"[✓] Connected to MongoDB {server_info['version']} {server_info['gitVersion'][:7]} at {db_address}:/{dbattrs['use_prod_db'] and 'administer' or 'administer_dev'} <RCN [{replica_state} {repl_status['set']}]>",
                32
            )
            logger.info("Connected to MongoDB %s %s at %s", server_info.get('version'), server_info.get('gitVersion', '')[:7], db_address)
        except Exception:
            il.cprint("[!] Mongo is not replicating", 33)
            logger.warning("Mongo is not replicating")
            il.cprint(
                f"[✓] Connected to MongoDB {server_info['version']} {server_info['gitVersion'][:7]} at {db_address}:/{dbattrs['use_prod_db'] and 'administer' or 'administer_dev'}",
                32
            )
            logger.info("Connected to MongoDB %s %s at %s", server_info.get('version'), server_info.get('gitVersion', '')[:7], db_address)
    def set(self, key: str | int, value: Any, db: str) -> None:
        assert isinstance(key, (str, int)), "key must be a string (integers accepted)!"
        assert isinstance(db, str), "db must be a string!"

        if db == self.APPS:
            key = str(key)

        collection = self.db[db]

        admin_id = str(key)

        # For places we prefer to store the place id as the MongoDB `_id`
        # and avoid duplicating it in `administer_id` when identical.
        if db == self.PLACES:
            # For places, identify documents by `_id` only.
            active_document = collection.find_one({"_id": admin_id})
        else:
            active_document = collection.find_one({"administer_id": admin_id})

        if active_document is not None:
            return collection.update_one({"_id": active_document["_id"]}, {"$set": {"data": value}})

        # Build new document. For places omit `administer_id` when it matches
        # the `_id` to avoid duplicate storage.
        if db == self.PLACES:
            new_doc = {"_id": admin_id, "data": value}
        else:
            new_doc = {"administer_id": admin_id, "data": value}

        return collection.insert_one(new_doc)

    def set_batch(self, items: Dict[str | int, dict], db: str) -> None:
        assert isinstance(items, dict), "items must be a dict!"
        assert isinstance(db, str), "db must be a string!"

        for k, v in items.items():
            self.set(k, v, db)

    def get(self, key: str | int, db: str) -> dict | None:
        assert isinstance(key, (str, int)), "key must be a string (integers accepted)"
        assert isinstance(db, str), "db must be an attr of db"

        admin_id = str(key)
        if db == self.PLACES:
            document = self.db[db].find_one({"_id": admin_id})
        else:
            document = self.db[db].find_one({"administer_id": admin_id})

        return document and document.get("data")

    def find(self, identifier: dict, db: str) -> str | None:
        assert isinstance(identifier, dict), "identifier must be a dict!"
        assert isinstance(db, str), "db must be a string!"

        document = self.db[db].find_one({f"data.{k}": v for k, v in identifier.items()})
        if not document:
            return None

        # For places return the `_id` (string); for others return `administer_id`.
        if db == self.PLACES:
            return document.get("_id")

        return document.get("administer_id")

    def delete(self, key: str | int, db: str) -> None:
        assert isinstance(key, (str, int)), "key must be a string or integer!"
        admin_id = str(key)
        if db == self.PLACES:
            self.db[db].delete_one({"_id": admin_id})
        else:
            self.db[db].delete_one({"administer_id": admin_id})

    def bulk_delete(self, keys: List[str | int], db: str) -> None:
        assert isinstance(keys, list), "keys must be a list! (try using db.delete())"
        if db == self.PLACES:
            ids = [str(k) for k in keys]
            self.db[db].delete_many({"_id": {"$in": ids}})
        else:
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
db = Database(dbattrs["use_prod_db"] and "administer" or "administer_dev")
web_database = None

if globals.dbattrs["use_prod_db"]:
    il.cprint("[!] Production database is enabled. Proceed with caution!", 35)
    try:
        logger
    except NameError:
        import logging
        logger = logging.getLogger(__name__)

    logger.warning("Production database is enabled")


def get_web_database():
    global web_database

    if web_database is None:
        web_database = Database("web")

    return web_database
