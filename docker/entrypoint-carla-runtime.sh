#!/usr/bin/env bash
set -e

if [ -x /carla_runtime/LinuxNoEditor/CarlaUE4.sh ]; then
  exec /carla_runtime/LinuxNoEditor/CarlaUE4.sh "$@"
elif [ -x /carla_runtime/CarlaUE4.sh ]; then
  exec /carla_runtime/CarlaUE4.sh "$@"
else
  echo "CARLA runtime not found under /carla_runtime" >&2
  echo "Mounted contents:" >&2
  ls -lah /carla_runtime >&2 || true
  find /carla_runtime -maxdepth 3 -name CarlaUE4.sh 2>/dev/null >&2 || true
  exit 1
fi