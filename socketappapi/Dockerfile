FROM python:3

RUN adduser quart --disabled-password 

WORKDIR /home/quart

RUN apt-get update -y

RUN apt-get upgrade -y

COPY socketappapi/requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt --upgrade 

COPY socketappapi/ /home/quart/

RUN chmod +x boot.sh 

ENTRYPOINT ["sh", "./boot.sh"]