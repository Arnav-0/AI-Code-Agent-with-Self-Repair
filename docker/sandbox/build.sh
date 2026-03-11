#!/bin/bash
set -e
echo 'Building Python sandbox image...'
docker build -t codeforge-sandbox-python:latest -f docker/sandbox/Dockerfile.python docker/sandbox/
echo 'Building Node.js sandbox image...'
docker build -t codeforge-sandbox-node:latest -f docker/sandbox/Dockerfile.node docker/sandbox/
echo 'All sandbox images built successfully!'
