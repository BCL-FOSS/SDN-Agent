FROM python:3

RUN adduser quart --disabled-password 

RUN apt-get update -y

RUN apt-get upgrade -y

WORKDIR /home/quart

COPY ubntmcp/requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt --upgrade 

COPY ubntmcp/ /home/quart/

RUN chmod +x boot.sh

ENTRYPOINT ["sh", "./boot.sh"]