FROM debian:stable-slim

RUN apt-get update && apt-get install -y curl jq

COPY client /client/

CMD ["bash", "/client/main.sh"]
