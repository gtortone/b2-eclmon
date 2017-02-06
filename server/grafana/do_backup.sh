#!/bin/bash

wizzy init
wizzy import orgs
wizzy import dashboards
wizzy import datasources

echo "Password replaced with a fake one (changeme)..."
for i in `grep --exclude=do_*,conf/wizzy.json -lR password *`; do sed -i 's|"password": "u50p4all"|' $i; done

echo "Files changed:"
grep --exclude=do_backup.sh -lR password *
