#!/bin/sh

while [ $1 ];do
  case $1 in
    'auto' )
      MODE=$1
      PROGRAM_NUMBER=$2
      shift 2
      ;;
    'manual' )
      MODE=$1
      shift
      ;;
    * )
      echo "Not a recognized parameter for service."
      exit 1
      ;;
  esac
done

/usr/bin/python3 /home/pi/raspb-scripts/heater_control.py $MODE $PROGRAM_NUMBER
