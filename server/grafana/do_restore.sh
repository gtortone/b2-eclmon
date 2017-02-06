#!/bin/bash

echo "insert password to use for datasources..."
read pwd

echo "please press return to confirm or CTRL-C to exit"
read

for i in `grep --exclude=do_* -lR password *`; do sed -i "s|\"password\": \"\(.*\)\"|\"password\": \"$pwd\"|" $i; done

wizzy init
wizzy export org 1
wizzy export dashboards
wizzy export datasources
