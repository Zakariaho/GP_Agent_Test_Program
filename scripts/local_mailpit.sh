#!/usr/bin/env bash
# Run the two Mailpit instances WITHOUT Docker (needs the `mailpit` binary on PATH:
# https://github.com/axllent/mailpit/releases). Stop with Ctrl-C.
mailpit -l 127.0.0.1:8025 -s 127.0.0.1:1025 &
mailpit -l 127.0.0.1:8026 -s 127.0.0.1:1026 &
wait
