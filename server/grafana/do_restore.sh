#!/bin/bash

echo "insert password to use for datasources..."
read pwd

echo "please press return to confirm or CTRL-C to exit"
read

for i in `grep --exclude=do_backup.sh,do_restore.sh,conf/wizzy.json -lR password *`; do sed -i "s|\"password\": \"\(.*\)\"|\"password\": \"$pwd\"|" $i; done

wizzy init
wizzy export org 1
wizzy export dashboards
wizzy export datasources

if [ "$HOSTNAME" = usopmon01 ]; then
   wizzy delete dashboard fuji-hall-ecl-endcap-monitoring-forward
   wizzy delete dashboard fuji-hall-ecl-endcap-temperature-histogram
   wizzy delete dashboard fuji-hall-ecl-endcap-relative-humidity-histogram
   wizzy delete dashboard test
fi
