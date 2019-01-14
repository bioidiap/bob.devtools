#!/usr/bin/env bash

if [[ `grep -c "www.idiap.ch" /etc/hosts` != 0 ]]; then
  echo "Not updating /etc/hosts - www.idiap.ch is already present..."
else
  echo "Updating /etc/hosts..."
  echo "" >> /etc/hosts
  echo "#We fake www.idiap.ch to keep things internal" >> /etc/hosts
  echo "172.31.100.235 www.idiap.ch" >> /etc/hosts
  echo "2001:620:7a3:600:0:acff:fe1f:64eb www.idiap.ch" >> /etc/hosts
fi
