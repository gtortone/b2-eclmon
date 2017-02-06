#!/bin/bash

wizzy init
wizzy import orgs
wizzy import dashboards
wizzy import datasources

echo "Password replaced with a fake one (changeme)..."
for i in `grep --exclude=do_* -lR password *`; do sed -i 's|"password": "\(.*\)"|"password": "changeme"|' $i; done

echo "Files changed:"
grep --exclude=do_backup.sh -lR password *
