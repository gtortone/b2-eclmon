#!/bin/bash

wizzy init
wizzy import orgs
wizzy import dashboards
wizzy import datasources

echo "Password replaced with a fake one (changeme)..."
for i in `grep --exclude=do_backup.sh,do_restore.sh,conf/wizzy.json -lR password *`; do sed -i 's|"password": "changeme"|' $i; done

echo "Files changed:"
grep --exclude=do_backup.sh -lR password *
