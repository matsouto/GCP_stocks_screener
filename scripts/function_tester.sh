#!/usr/bin/bash

functions-framework --port 8080 --target screener_run --signature-type http --source main.py --debug

# curl -X POST \
# -H "Content-type:application/json" \
# -d  '{"num_1":20, "num_2": 30}' \
# -w '\n' \
# http://localhost:8080