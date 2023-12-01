// whatsapp.js (Recibe las comunicaciones del servidor y las envia a whatsapp-web.js para enviar y recibir videos)
// Autor: Peduzzi Acevedo Gustavo Alain
// Fecha: 2023-05-25

import fs from "fs";
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

			const data_base64 = {
				data: "",
				mimetype: "",
			};
			
			switch (msg.type) {
				case MessageTypes.TEXT:
					data_base64.data = Buffer.from(msg.body).toString("base64");
					data_base64.mimetype = "text/plain";
					break;
				case MessageTypes.IMAGE: 
				case MessageTypes.VIDEO:
					if (msg.hasMedia === false) {
						console.error("Message has no media");
						await msg.reply("Mensaje no tiene media");
						return;
					}
					let media = await msg.downloadMedia();
					if (media === undefined) {
						console.error("Media is undefined");
						await msg.reply("Media es undefined");
						return;
					}
					data_base64.data = media.data
					data_base64.mimetype = media.mimetype;
					break;
				default:
					console.warn("Message type not supported");
					await msg.reply("Mensaje no soportado");
					return;
			}


			await this.sendDataByChunks(data_base64.data, data_base64.mimetype)
			.catch(async err => {
				console.error("Error sending video", err);
				await msg.reply("Error al enviar el video al servidor");
			});
		});
		this.client.initialize();
	}
	
	async sendDataByChunks(data_base64, mimetype, CHUNK_SIZE = 512 * 1024) {
		return new Promise(async (resolve, reject) => {
			const uuid = crypto.createHash('md5').update(data_base64).digest('hex').substring(0, 16);
			
			this.socket.emit("video-start", uuid, mimetype, data_base64.length);
	
			const sendChunk = async (chunk_index) => {
			    const start = chunk_index * CHUNK_SIZE,
					  end = Math.min(data_base64.length, start + CHUNK_SIZE),
					  chunk = data_base64.substring(start, end);
	
			    // Esperar confirmación o timeout
			    return new Promise((resolve, reject) => {
					let timer, expected_chunk_index = chunk_index;
	
			        const listener = ({data_uuid, chunk_index: confirmed_chunk_index}) => {
			            if (data_uuid === uuid && confirmed_chunk_index === expected_chunk_index) {
							this.socket.off('video-chunk-ack', listener);
							clearTimeout(timer);
			                return resolve();
			            }
			        };

					timer = setTimeout(() => {
						this.socket.off('video-chunk-ack', listener);
			            reject(new Error("Timeout waiting for chunk confirmation"));
			        }, 10*1000); // 10 segundos de timeout
					
					this.socket.on('video-chunk-ack', listener);
					this.socket.emit('video-chunk', uuid, chunk_index, chunk);
	
					
			    });
			};
	
			for (let i = 0, current_chunk_index = 0; 
				 i < data_base64.length; 
				 i += CHUNK_SIZE
			) {
				console.log(`Sending chunk ${i / CHUNK_SIZE + 1} of ${Math.ceil(data_base64.length / CHUNK_SIZE)}`);
			    let success = false;
			    let attempts = 0;
	
			    while (!success && attempts < 3) {
			        try {
						console.log(`Sending chunk ${i / CHUNK_SIZE + 1} of ${Math.ceil(data_base64.length / CHUNK_SIZE)} tries ${attempts + 1}/3`);
			            await sendChunk(current_chunk_index);
			            success = true;
			        } catch (error) {
			            console.error(`Error sending chunk ${current_chunk_index+1}:`, error.message);
			            attempts++;
			        }
			    }
	
			    if (!success) {
			        console.error(`Failed to send chunk ${current_chunk_index} after 3 attempts`);
					return reject("Failed to send chunk");
			    }

			    current_chunk_index++;
			}
			// listener = ({data_uuid}) => {
			// 	if (data_uuid === uuid) {
			// 		this.socket.off('data-end-ack', listener);
			// 	}
			// };
			// this.socket.on('data-end-ack', listener);
			this.socket.emit('data-end', uuid);
			console.log("All data sent");
			return resolve(true);
		});

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
			let messageMedia = MessageMedia.fromFilePath(filename);
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