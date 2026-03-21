# pyxfluff 2025

from .. import db

from nanoid import generate

import logging
logger = logging.getLogger(__name__)

print("Testing a READ command.")
logger.info("Testing a READ command")
db.get_all(db.PLACES)

print("Success!")
logger.info("DB tools success")

if input("Would you like to generate an admin key? If you are adding a new node to an AOS cluster, you do not need this. ([y]es/[n]o) > ").lower().strip() in ["y", "yes"]:
    secret = f"ADM-_TOK-_{generate(size=75)}"

    db.set("__ENV_AUTH__", secret, db.SECRETS)

    print(f"[✓] Your database is functional!\n     > Your secret key is `{secret}`. You can use this key to publish apps and complete administrative tasks.\n\n    Please note this key only applies to whatever database is active (config.database.is_prod_db). If you use your development database, you'll need a new key, which you can generate with `aos database genkeys`.")
    logger.info("Generated admin secret key")
else:
    print("[✓] Your database is functional!")
    logger.info("Database functional (no key generated)")
