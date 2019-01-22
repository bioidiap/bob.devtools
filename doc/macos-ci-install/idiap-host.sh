#!/usr/bin/env bash

if [[ `grep -c "www.idiap.ch" /etc/hosts` != 0 ]]; then
  echo "Not updating /etc/hosts - www.idiap.ch is already present..."
else
  echo "Updating /etc/hosts..."
  echo "" >> /etc/hosts
  echo "#We fake www.idiap.ch to keep things internal" >> /etc/hosts
  echo "What is the internal server IPv4 address?"
  read ipv4add
  echo "${ipv4add} www.idiap.ch" >> /etc/hosts
  echo "What is the internal server IPv6 address?"
  read ipv6add
  echo "${ipv6add} www.idiap.ch" >> /etc/hosts
fi
