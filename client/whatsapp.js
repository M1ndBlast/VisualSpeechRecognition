// whatsapp.js (Recibe las comunicaciones del servidor y las envia a whatsapp-web.js para enviar y recibir videos)
// Autor: Peduzzi Acevedo Gustavo Alain
// Fecha: 2023-05-25

import fs from "fs";
import { v4 as uuidv4 } from "uuid";
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
				case MessageTypes.IMAGE:
				case MessageTypes.VIDEO:
					const media = await msg.downloadMedia();
					console.log("Media received: ", media.mimetype, media.data.substring(0, 100));
					this.socket.emit("media", { mimetype: media.mimetype, data: media.data});
					break;
				default:
					console.warn("Message type not supported");
					break;
			}
		});
		this.client.initialize();
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

	sendImage(image) { // Recibe imagen en base64 y genera un MessageMedia para enviarlo
		// Guardar el archivo como client.png
		// let filename = "client.png";
		// let image_buf = Buffer.from(image, "base64");

		// fs.writeFile(filename, image_buf, async (err) => {
		// 	if (err) {
		// 		console.error(err);
		// 		return;
		// 	}
		// 	console.log("File saved");
		// 	// let messageMedia = new MessageMedia("video/mp4", video, "foo" + ".mp4");
		// 	let messageMedia = MessageMedia.fromFilePath(filename);
		// 	this.client.sendMessage("5215610338516@c.us", messageMedia, {
		// 		caption: "Imagen recibida",
		// 	}).catch(err => console.error("ERROR Catched",err));
		// });
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