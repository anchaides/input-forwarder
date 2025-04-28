#!/bin/bash 
export PATH="$(pwd)/wayland_client:$PATH" 
PYTHONPATH=/home/anchaides/Dev/input-forwarder/ WAYLAND_DEBUG=1  KEYBOARD="SINO WEALTH Gaming KB" MOUSE="Razer Razer Viper" python3 -m input_forwarder  
