#!/bin/bash
D=$(date +%F_%H-%M)
B="/mnt/backups/mongodb/adm_prod/dump_$D"
WEBHOOK_URL=""

mkdir -p "$B"
sshfs Pyx@192.168.0.40:/mnt/backups /mnt/backups # sorry that this is hardcoded, you can fix it yourself

echo "[-] Backing up $D"
docker exec mongodb8 mongodump --out /backup > /tmp/mongo.log 2>&1
docker cp mongodb8:/backup "$B"

echo "[-] Cleaning up"
find /mnt/backups/mongodb -mindepth 1 -maxdepth 1 -type d -mtime +14 -exec rm -rf {} +
umount /mnt/backups

DESC=$(printf "Here are the logs:\n``$(\n%s\n)``" "$(cat /tmp/mongo.log)")

curl -H "Content-Type: application/json" -X POST -d @- "$WEBHOOK_URL" <<EOF
{
  "content": null,
  "embeds": [{
    "title": ":white_check_mark: Database Backup Success",
    "description": $DESC,
    "color": null,
    "author": {
      "name": "AOS Database Backup Service",
      "icon_url": "https://avatars.githubusercontent.com/u/194324847?s=200&v=4"
    },
    "footer": {
      "text": "Data processed on db-us-3"
    }
  }],
  "attachments": []
}
EOF


echo "[ok] Done!"
