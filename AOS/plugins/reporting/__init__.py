# pyxfluff 2025

# This script was previously internal only but now that everybody can host AOS it is open-source.
# I know it's ugly and `start` is wrong so I am working to fix it

from collections import Counter
from AOS.plugins.database import db

import matplotlib.pyplot as plt

# start = 20019
x, y, fy = [], [], []

data = db.get_all(db.REPORTED_VERSIONS)


def daily_usage_graph():
    x, y = [], []

    for day in data:
        try:
            z = day["data"]["live"]
        except KeyError:
            continue

        x.append(int(day["administer_id"]))
        y.append(day["data"]["live"])

    y2 = [item.get("1.2", 0) for item in y]
    y3 = [item.get("1.2.1", 0) for item in y]
    y4 = [item.get("1.2.2", 0) for item in y]
    y5 = [item.get("1.2.3", 0) for item in y]
    y6 = [item.get("2.0", 0) for item in y]
    y = [item.get("1.1.1", 0) for item in y]

    plt.plot(x, y, marker="o")
    plt.plot(x, y2, marker="*")
    plt.plot(x, y3, marker="o")
    plt.plot(x, y4, marker="o")
    plt.plot(x, y5, marker="o")
    plt.plot(x, y6, marker="o")

    # Add labels and title
    plt.ylabel("Place Starts")
    plt.xlabel("Day (Unix time)")
    plt.title("Administer usage over the LIVE branch")
    plt.legend(["1.1.1", "1.2", "1.2.1", "1.2.2", "1.2.3", "2.0"])


def overall_places():
    x = []
    y = []

    for day in data:
        db_key: str = day["administer_id"]
        if db_key.startswith("day-"):
            day_number = int(db_key.split("-")[1])
            places_len = day["data"].get("places_len", 0)

            x.append(day_number)
            y.append(places_len)

    plt.plot(x, y, marker="o", label="Overall Places")

    plt.ylabel("Places")
    plt.xlabel("Day")
    plt.title("Number of Administer-powered games over time")
    plt.legend()

def sort(x, y, **kw):
    x, y = zip(*sorted(zip(x, y)))
    plt.plot(x, y, **kw)

def combined():
    x, y = [], []
    for day in data:
        try:
            x.append(int(day["administer_id"]))
            y.append(
                {
                    **day["data"].get("live", {}),
                    **day["data"].get("beta", {}),
                    **day["data"].get("stable", {})
                }
            )
        except Exception:
            continue

    for version, y_vals in {
        "1.1.1": [item.get("1.1.1", 0) for item in y],
        "1.2": [item.get("1.2", 0) for item in y],
        "1.2.1": [item.get("1.2.1", 0) for item in y],
        "1.2.2": [item.get("1.2.2", 0) for item in y],
        "1.2.3": [item.get("1.2.3", 0) for item in y],
        "2.0.0": [item.get("2.0.0", 0) for item in y]
    }.items():
        sort(x, y_vals, marker="o", label=version)

    x2, y2 = [], []
    for day in data:
        db_key = day["administer_id"]

        if db_key.startswith("day-"):
            x2.append(int(db_key.split("-")[1]))
            y2.append(day["data"].get("places_len", 0))

    sort(x2, y2, marker="*", label="Overall Places")
    plt.xlabel("Day (missing some data)")
    plt.ylabel("Total Places")
    plt.legend()


def home_nodes():
    places = db.get_all(db.PLACES)

    nodes = [
        place["data"].get("HomeNode")
        for place in places
        if "data" in place and "HomeNode" in place["data"]
    ]

    values = [
        Counter(nodes).get(n, 0)
        for n in ["aos-canary", "us-1", "us-2", "us-3", "eur-1"]
    ]
    versions = [
        f"{n} ({Counter(nodes).get(n, 0)})"
        for n in ["aos-canary", "us-1", "us-2", "us-3", "eur-1"]
    ]

    plt.bar(versions, values)
    plt.xlabel("Node Name (Usage Count)")
    plt.ylabel("Adoption")
    plt.title("AOS Node Usage")
    plt.xticks(rotation=45)


# daily_usage_graph()
# overall_places()
combined()
# home_nodes()

plt.tight_layout()
plt.savefig("/home/Pyx/adm/Log")

plt.show()

exit(0)
