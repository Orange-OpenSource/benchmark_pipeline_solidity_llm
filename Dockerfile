FROM debian:latest

RUN apt-get update && apt-get install -y software-properties-common

# solc
COPY solc-static-linux /usr/bin/solc
RUN chmod +x /usr/bin/solc

# python
RUN apt-get install -y python3 python3-pip python3-venv


WORKDIR /app

RUN python3 -m venv venv

RUN . venv/bin/activate && pip3 install pandas && pip3 install yaspin && pip3 install requests

# slither
RUN . venv/bin/activate && pip3 install slither-analyzer 

# npm
RUN apt-get install nodejs npm -y

RUN npm i npx

# hardhat
RUN npm install --save-dev hardhat

# zip
RUN apt-get install zip -y

# solc-select
RUN git clone https://github.com/crytic/solc-select.git /opt/solc-select && \
    cd /opt/solc-select && \
    python3 setup.py install

ENV PATH="/root/.local/bin:$PATH"

# solc
RUN solc-select install 0.8.25
RUN solc-select use 0.8.25

ENV SOLC_VERSION=0.8.25

COPY . .

RUN cd hardhat_test_env && npm install

# requirements
RUN . venv/bin/activate && pip3 install -r requirements.txt

CMD ["sh", "-c", ". venv/bin/activate && python3 main.py"]
