# Base image
FROM ubuntu:latest

# Add your instructions here
RUN apt-get update && apt-get install -y curl unzip 

# Fix for "ImportError: libGL.so.1: cannot open shared object file: No such file or directory"
RUN apt-get install libgl1-mesa-glx -y

# Install Node.js
RUN curl -sL https://deb.nodesource.com/setup_18.x | bash -
RUN apt-get update && apt-get install -y nodejs

# Install Python 3.8
RUN apt-get update && apt-get install -y python3.8


# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./
RUN npm install

# Copy requirements.txt
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Fix for "TypeError: Cannot read properties of undefined (reading 'data')"
RUN sed -i '445s/|| msg.mediaData.mediaStage === '\''FETCHING'\''//' node_modules/whatsapp-web.js/src/structures/Message.js

# Download repo
RUN git clone https://github.com/mpc001/Visual_Speech_Recognition_for_Multiple_Languages.git server/vsr

# Change line from server/vsr/configs/CMUMOSEAS_V_ES_WER44.5.ini:3 data_path with "/app/server/vsr/"
RUN sed -i 's|benchmarks/CMUMOSEAS/|/app/server/vsr/&|g' server/vsr/configs/CMUMOSEAS_V_ES_WER44.5.ini

RUN curl -L -o lm.zip https://transfer.sh/fCfpvTlioz/lm_es.zip && \
	unzip lm.zip -d server/vsr/benchmarks/CMUMOSEAS/language_models/es && \
	rm lm.zip
RUN curl -L -o model.zip https://transfer.sh/PWGO6K55yN/CMUMOSEAS_V_ES_WER44.5.zip && \
	unzip model.zip -d server/vsr/benchmarks/CMUMOSEAS/models/es && \
	rm model.zip




# Copy the rest of the application code
COPY . .

# Specify the command to run the application
CMD [ "npm", "run", "watch:client", "&", "npm", "run", "watch:server" ]
