#!/bin/bash
docker build -f infra/dockerfiles/Dockerfile.api --progress=plain --no-cache -t test-api ./api 2>&1 | tee /tmp/build_log.txt
