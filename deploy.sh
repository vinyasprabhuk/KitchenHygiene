#!/bin/bash
# Deploy script for Kitchen Hygiene on cPanel. Run manually or via
# .cpanel.yml's Deploy HEAD Commit. Each step echoes clearly so a partial
# failure shows exactly where it stopped, instead of failing silently.
#
# Uses the venv's own python/pip by absolute path throughout -- a bare
# `python3` here can silently resolve to system Python instead of the
# venv (no Flask installed there), which would crash tools/init_db.py
# with no clear signal why deploy "did nothing".
set -e

VENV=/home/wattsupc/virtualenv/hygiene.mokshamveg.com/3.11

echo "== Kitchen Hygiene deploy starting =="

echo "-- Installing dependencies --"
"$VENV/bin/pip" install -q -r requirements.txt
echo "   done"

echo "-- Ensuring database schema --"
"$VENV/bin/python3" tools/init_db.py
echo "   done"

echo "-- Applying migrations --"
"$VENV/bin/python3" tools/migrate_all.py
echo "   done"

echo "-- Restarting app --"
mkdir -p tmp
touch tmp/restart.txt
echo "   done"

echo "== Deploy complete =="
