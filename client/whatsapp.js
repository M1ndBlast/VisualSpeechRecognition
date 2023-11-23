// whatsapp.js (Recibe las comunicaciones del servidor y las envia a whatsapp-web.js para enviar y recibir videos)
// Autor: Peduzzi Acevedo Gustavo Alain
// Fecha: 2023-05-25

import fs from "fs";
import { v4 as uuidv4 } from "uuid";
import crypto from "crypto";
import Whatsapp from 'whatsapp-web.js'
const { Client, LocalAuth, MessageTypes, MessageMedia } = Whatsapp

import qrcode from "qrcode-terminal";
import Console from "./mConsole.js";
const console = new Console("[whatsapp client]");

class WhatsappClient {
	constructor(socket) {
		this.socket = socket;
		this.client = new Client({
			authStrategy: new LocalAuth(),
			puppeteer: {
				// headless: false,
			}
		});
		this.client.on("qr", (qr) => {
			qrcode.generate(qr, { small: true });
		});
		this.client.on("ready", () => {
			console.log("Conectado");
			this.client.sendMessage("5215610338516@c.us", "Conectado 👌");
		});
		this.client.on("message", async (msg) => {
			if (!this.socket.active) {
				console.error("Socket is not active");
				return;
			}

			switch (msg.type) {
				case MessageTypes.TEXT:
					console.log("Message received: ", msg.body);
					this.socket.emit("text", msg.body);
					break;
				case MessageTypes.IMAGE: {
					let media = await msg.downloadMedia();
					console.log("Media received: ", media.mimetype, media.data.substring(0, 100));
					this.socket.emit("media", { mimetype: media.mimetype, data: media.data});
					break;
				}
				case MessageTypes.VIDEO: {
					let media = await msg.downloadMedia();
					console.log(msg.from);
					if (!media) {
						console.error("Error downloading media");
						await msg.reply("Error al descargar el video");
						return;
					}
					console.log("Media received: ", media.mimetype, media.data.substring(0, 100));
            		await this.sendVideoInChunks(media.data, media.mimetype).catch(async err => {
						console.error("Error sending video", err);
						await msg.reply("Error al enviar el video al servidor");
					});
					break;
				}
				default:
					console.warn("Message type not supported");
					break;
			}
		});
		this.client.initialize();
	}
	
	async sendVideoInChunks(data, mimetype) {
		const CHUNK_SIZE = 512 * 1024; // 512KB = 0.5MB
		// const id = uuidv4().replace(/-/g, "").substring(0, 16);
		const id = crypto.createHash('md5').update(data).digest('hex').substring(0, 16);



		let chunkIndex = 0;

		this.socket.emit("video-start", id, mimetype, data.length);


		const sendChunk = async (index) => {
            let start = index * CHUNK_SIZE;
            let end = Math.min(data.length, start + CHUNK_SIZE);
			let chunk = data.substring(start, end);

            // Esperar confirmación o timeout
            return new Promise((resolve, reject) => {
				let timer = setTimeout(() => {
                    this.socket.off('video-chunk-ack', listener);
                    reject(new Error("Timeout waiting for chunk confirmation"));
                }, 10000); // 10 segundos de timeout

                const listener = ({data_uuid, chunk_index: confirmed_chunk_index}) => {
                    if (data_uuid === id && confirmed_chunk_index === index) {
                        this.socket.off('video-chunk-ack', listener);
						clearTimeout(timer);
                        return resolve();
                    }
                };

                this.socket.on('video-chunk-ack', listener);
				this.socket.emit('video-chunk', id, index, chunk.toString('base64'));

                
            });
        };

		for (let i = 0; i < data.length; i += CHUNK_SIZE) {
            let success = false;
            let attempts = 0;

            while (!success && attempts < 3) {
                try {
					console.log(`Sending chunk ${i / CHUNK_SIZE + 1} of ${Math.ceil(data.length / CHUNK_SIZE)} tries ${attempts + 1}/3`);
                    await sendChunk(chunkIndex);
                    success = true;
                } catch (error) {
                    console.error(`Error sending chunk ${chunkIndex}:`, error);
                    attempts++;
                }
            }

            if (!success) {
                console.error(`Failed to send chunk ${chunkIndex} after 3 attempts`);
				return Promise.reject("Failed to send chunk");
                break; // Detener el envío de más fragmentos
            }

            chunkIndex++;
        }

		console.log("Video sent");
    }

	sendMessage(message) {
		this.client.sendMessage("5215610338516@c.us", message)
	}

	sendVideo(video) {
		// Guardar el archivo como client.mp4
		let filename = "client.mp4";
		let video_buf = Buffer.from(video, "base64");

		fs.writeFile(filename, video_buf, async (err) => {
			if (err) {
				console.error(err);
				return;
			}
			console.log("File saved");
			// let messageMedia = new MessageMedia("video/mp4", video, "foo" + ".mp4");
			let messageMedia = MessageMedia.fromFilePath(filename);
			console.log("foo");
			await this.client.sendMessage("5215610338516@c.us", messageMedia, {
				caption: "Video recibido",
			});
		});

	}

	// Recibe imagen en base64 y genera un MessageMedia para enviarlo al usuario
	sendImage(image) { 
		let messageMedia = /* await */ new MessageMedia("image/png", image, "foo" + ".png");
		this.client.sendMessage("5215610338516@c.us", messageMedia, {
			caption: "Imagen recibida",
		}).catch(err => console.error("ERROR cachadoooo", err));
	}

	stop() {
		this.client.destroy();
	}
}

// to import use: import myWhatsapp from "./myWhatsapp.js";
export default WhatsappClient;