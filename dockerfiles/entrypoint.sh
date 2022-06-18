#!/bin/bash

set -e

if [ "$1" = 'server' ]; then
  shift
  # Figure out public address
  export GHIDRA_PUBLIC_HOSTNAME=${GHIDRA_PUBLIC_HOSTNAME:-0.0.0.0}
  echo HOSTNAME=${GHIDRA_PUBLIC_HOSTNAME}

  # Add users
  GHIDRA_USERS=${GHIDRA_USERS:-admin}
  if [ ! -e "/repos/users" ] && [ ! -z "${GHIDRA_USERS}" ]; then
    mkdir -p /repos/~admin
    for user in ${GHIDRA_USERS}; do
      echo "Adding user: ${user}"
      echo "-add ${user}" >> /repos/~admin/adm.cmd
    done
  fi

  exec "/ghidra/server/ghidraSvr" console
fi

exec "$@"
