#!/usr/bin/env bash
trap 'kill $(jobs -p)' EXIT

mkdir -p secret
[ -f /secret/secret_key ] || echo "secret" > secret/secret_key
[ -f /secret/aws_creds ] || echo "," > secret/aws_creds
mkdir -p logs
rollup --watch -c > logs/rollup.log  2>&1 &
./scss_watch.sh > logs/sass.log 2>&1 &
python3 main.py --debug
