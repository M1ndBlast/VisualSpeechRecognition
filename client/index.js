// index.js (Comunicacion con el servidor mediante socket.io y uso de myWhatsapp.js con whatsapp-web.js para recibir y enviar videos)
// Autor: Peduzzi Acevedo Gustavo Alain
// Fecha: 2023-05-25
// Descripcion: Archivo principal del cliente, se encarga de la comunicacion con el servidor mediante socket.io y el uso de nuestro archivo myWhatsapp.js con la biblioteca whatsapp-web.js para recibir y enviar videos

import { io } from "socket.io-client";
import WhatsappClient from "./whatsapp.js";
import Console from "./mConsole.js";
const console = new Console("[socket client]");

const socket = io("http://localhost:8080");
const whatsapp = new WhatsappClient(socket);


socket.on("connect", () => {
	console.log("Conectado");
});

socket.on("disconnect", () => {
	console.log("Desconectado");
	//   whatsapp.stop();
});

socket.on("*", (event, ...args) => {
	console.log("*", event, args);
});

socket.on("text", (message) => {
	console.log("socket sent text");
	whatsapp.sendMessage(message);
});

socket.on("media", (res) => { // res = { mimetype, data }
	console.log("socket sent media");
	let { mimetype, data } = res;
	console.log(mimetype, data.substring(0, 100));

	if (mimetype.includes("video")) {
		whatsapp.sendVideo(data);
	} else if (mimetype.includes("image")) {
		whatsapp.sendImage(data);
	} else {
		whatsapp.sendMessage("No se pudo procesar el archivo :(");
	}
});

socket.on("video", (video) => {
	console.log("socket sent video");
	console.log(video.substring(0, 100));
	whatsapp.sendVideo(video);
});

socket.on("image", (image) => {
	console.log("socket sent image");
	console.log(image.substring(0, 100));
	whatsapp.sendImage(image);
});