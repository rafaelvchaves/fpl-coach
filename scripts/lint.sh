#!/usr/bin/env bash

find ../src -type f -name "*.py" | xargs pylint
