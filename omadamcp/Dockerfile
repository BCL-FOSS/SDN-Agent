FROM python:3

RUN adduser quart --disabled-password 

RUN apt-get update -y

RUN apt-get upgrade -y

WORKDIR /home/quart

RUN mkdir /home/quart/instance

RUN mkdir /home/quart/instance/apps

COPY omadamcp/requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY omadamcp/ /home/quart/

RUN chmod +x boot.sh

ENTRYPOINT ["sh", "./boot.sh"]