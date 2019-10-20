#!/bin/sh

while [ $1 ];do
  case $1 in
    'auto' )
      MODE=$1
      PROGRAM_NUMBER=$2
      shift
      ;;
    'manual' )
      MODE=$1
      shift
      ;;
  esac
done

/usr/bin/python3 /home/pi/raspb-scripts/heater_control.py $MODE $PROGRAM_NUMBER
