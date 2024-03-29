# Base image
FROM ubuntu:20.04

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./
COPY requirements.txt ./

# Add your instructions here
RUN apt-get update &&\
	apt-get install -y\
		curl unzip libgl1-mesa-glx &&\
	curl -sL https://deb.nodesource.com/setup_18.x | bash - &&\
	apt-get update && apt-get install -y \
		nodejs python3.8 python3-pip git &&\
	apt-get clean
RUN npm install
	# pip install -r requirements.txt
	# Download repo
RUN	git clone https://github.com/mpc001/Visual_Speech_Recognition_for_Multiple_Languages.git server/vsr &&\
	pip install torch torchvision torchaudio \
				opencv-python \
				scipy \
				scikit-image \
				av \
				six \
				mediapipe \
				ffmpeg-python \
				openai \
				python-socketio \
				openpyxl \
				numpy \
				opencv-python

# pip install -r server/vsr/requirements.txt

RUN curl -L -o lm.zip https://transfer.sh/fCfpvTlioz/lm_es.zip && \
	unzip lm.zip -d server/vsr/benchmarks/CMUMOSEAS/language_models/es && \
	rm lm.zip &&\
	curl -L -o model.zip https://transfer.sh/PWGO6K55yN/CMUMOSEAS_V_ES_WER44.5.zip && \
	unzip model.zip -d server/vsr/benchmarks/CMUMOSEAS/models/es && \
	rm model.zip

	# Fix for "TypeError: Cannot read properties of undefined (reading 'data')"
RUN sed -i '445s/|| msg.mediaData.mediaStage === '\''FETCHING'\''//' node_modules/whatsapp-web.js/src/structures/Message.js &&\
	# Change line from server/vsr/configs/CMUMOSEAS_V_ES_WER44.5.ini:3 data_path with "/app/server/vsr/"
	sed -i 's|benchmarks/CMUMOSEAS/|/app/server/vsr/&|g' server/vsr/configs/CMUMOSEAS_V_ES_WER44.5.ini

# Copy the rest of the application code
COPY . .

# Specify the command to run the application
CMD [ "npm", "run", "watch:client", "&", "npm", "run", "watch:server" ]
