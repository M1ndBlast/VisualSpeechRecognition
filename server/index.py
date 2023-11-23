# index.js (Comunicacion con el cliente mediante socket.io para recibir y enviar videos)
# Autor: Peduzzi Acevedo Gustavo Alain
# Fecha: 2023-05-25

from aiohttp import web
import base64
import socketio
import openai
import face_landmarker
import time
openai.api_key = "sk-nX..."

sio = socketio.AsyncServer()
app = web.Application()
sio.attach(app)
clients = []

def generar_respuesta(texto):
	# Generar respuesta utilizando Whisper
	respuesta = openai.Completion.create(
		#model="gpt-3.5-turbo",
		model="text-davinci-003",
		prompt=f'<persona>{texto}</persona>\n<asistente>',
		stop=["</asistente>"],
		max_tokens=1000,
	)
	if respuesta.choices[0].finish_reason == 'length':
		print(f'finish reason {respuesta.choices[0].finish_reason}')
		
	respuesta = respuesta.choices[0].text
	# Parsear acentos y caracteres especiales que estan en \uXXXXdd
	respuesta = respuesta.strip().encode('latin1').decode('unicode_escape')
	return respuesta


@sio.event
def connect(sid, environ):
	clients.append(sid)
	print(f"connect   \t[{len(clients)}]\t{sid}")
	
@sio.event
def disconnect(sid):
	clients.remove(sid)
	print(f"disconnect\t[{len(clients)}]\t{sid}")
	
@sio.on('*')
async def catch_all(event, sid, data):
	print('catch_all ', event, data)

@sio.event
async def text(sid, data):
	print("message ", data)
	data = generar_respuesta(data)
	await sio.emit('text', data)
	
@sio.event
async def media(sid, req): # req = { mimetype: 'image/png', data: 'base64 encoded data' }
	mimetype = req['mimetype']
	data = req['data']

	print("media ", mimetype, data[:100])

	if mimetype.startswith('image/'):
		print("image ", data[:100])
		filename = f'image.{mimetype.split("/")[1]}'
			
		with open(filename, 'wb') as f:
			f.write(base64.b64decode(data))

		try:
			# Detectar rostros
			face_landmarker.landmark_image(filename)

			# Enviar rostros detectados
			with open('landmark.jpg', 'rb') as f:
				# await sio.emit('image', base64.b64encode(f.read()).decode('ascii'))
				await sio.emit('image', base64.b64encode(f.read()).decode('utf-8'))
			with open('croped.jpg', 'rb') as f:
				# await sio.emit('image', base64.b64encode(f.read()).decode('ascii'))
				await sio.emit('image', base64.b64encode(f.read()).decode('utf-8'))
		except Exception as e:
			print(e)
			await sio.emit('text', 'No se detectaron rostros')
		return

	elif mimetype.startswith('video/'):
		print("video ", data[:100])
			
		with open(f'video.{mimetype.split("/")[1]}', 'wb') as f:
			f.write(base64.b64decode(data))
	else:
		print("unknown media type ", mimetype)

	await sio.emit('media', { 'mimetype': mimetype, 'data': data})
	
@sio.event
async def image(sid, data): # data in base64 encoded
	print("image ", data[:100])

	await sio.emit('image', data)

@sio.event
async def video(sid, data): # data in base64 encoded
	print("video ", data[:100])
	
	await sio.emit('video', data)

data_transactions = {}

@sio.on('video-start')
async def handle_video_start(sid, id, mimetype, total_buffer):
	print(f"Recibiendo video {id} de tipo {mimetype} en fragmentos de {total_buffer} bytes")
	data_transactions[id] = { 'mimetype': mimetype, 'total_buffer': total_buffer, 'chunks': {} }

video_chunks = {}
@sio.on('video-chunk')
async def handle_video_chunk(sid, data_uuid, chunk_index, chunk):
	print(f"Recibido fragmento {chunk_index} de {len(chunk)} bytes")

	if data_uuid not in data_transactions:
		print("Error: no se ha recibido el fragmento de inicio")
		return

	# Almacenar cada fragmento en un diccionario con el índice como clave
	data_transactions[data_uuid]['chunks'][chunk_index] = chunk

	# Enviar un ACK al cliente para indicar que el fragmento ha sido recibido
	await sio.emit('video-chunk-ack', { 'data_uuid': data_uuid, 'chunk_index': chunk_index})


	# Si todos los fragmentos han llegado, reconstruir y procesar el video
	if got_all_chunks(data_transactions[data_uuid]['chunks'], data_transactions[data_uuid]['total_buffer']):
		print(f"Todos los fragmentos recibidos, procesando video {data_uuid}")
		video_chunks = data_transactions[data_uuid]['chunks']
		video_completo = ''.join([video_chunks[i] for i in sorted(video_chunks.keys())])
		procesar_video(video_completo)
		del data_transactions[data_uuid]
		await sio.emit('text', "Video recibido y procesado :D")

def got_all_chunks(chunks, total_buffer):
	"""
	Verificar si todos los fragmentos ya han sido recibidos y concuerdan con el tamaño esperado (total_buffer)
	"""
	if len(chunks) == 0:
		return False

	# Verificar si todos los fragmentos han sido recibidos
	if len(chunks) != max(chunks.keys()) + 1:
		return False

	# Verificar si la suma de los tamaños de los fragmentos concuerda con el tamaño esperado
	# print(f"Suma de tamaños de fragmentos: {sum([len(chunks[i]) for i in chunks.keys()])} vs {total_buffer}")
	if sum([len(chunks[i]) for i in chunks.keys()]) != total_buffer:
		return False

	return True

def procesar_video(video_base64):
	# Convertir el video de Base64 a bytes
	video_bytes = base64.b64decode(video_base64)

	# Guardar el video en un archivo
	with open("video_recibido.mp4", "wb") as video_file:
		video_file.write(video_bytes)

	# Aquí puedes agregar lógica adicional para procesar el video
	# Por ejemplo, analizar el video, extraer metadatos, realizar reconocimiento facial, etc.

	print("Video procesado y guardado como 'video_recibido.mp4'")


	

if __name__ == '__main__':
	try:
		web.run_app(app)
	except KeyboardInterrupt:
		print('Exiting...')
		exit(0)