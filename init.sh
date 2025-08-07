#!/bin/bash
# init for agentik

dockersetup() {

  sudo docker-compose build --no-cache 

  sudo docker volume create --name=app_agentik_data
  sudo docker-compose up

}

sudo apt-get update -y
sudo apt-get upgrade -y

dockersetup

