#!/usr/bin/bash

gcloud functions deploy screener_run \
--runtime python39 \
--set-secrets 'CREDENTIALS=projects/66915811604/secrets/screener_bot_credentials/versions/latest' \
--trigger-http