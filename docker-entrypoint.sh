#!/bin/bash

case $1 in
  server)
    echo "Running $1"
    python3 main.py --type "$1"
    ;;
  client)
    echo "Running $1"
    python3 main.py --type "$1"
    ;;
  *)
    echo "Unknown application type"
    ;;
esac
