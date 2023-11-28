# Autor: Peduzzi Acevedo Gustavo Alain
# Fecha: 2023-05-25

import sys
# caution: path[0] is reserved for script path (or '' in REPL)
sys.path.append('/workspaces/VisualSpeechRecognition/server/vsr') 
sys.path.append('/workspaces/VisualSpeechRecognition/server') 

import os
import base64
import openai
import socketio
import face_landmarker

sio = socketio.Server()
app = socketio.WSGIApp(sio)

clients = []
data_transactions = {}


@sio.on('*')
def catch_all(event, sid, data):
	print(f'catch_all  \t{event}\t{sid}\t{data}')

@sio.event
def connect(sid, environ):
	clients.append(sid)
	print(f"connect   \t[{len(clients)}]\t{sid}")

@sio.event
def disconnect(sid):
	clients.remove(sid)
	print(f"disconnect\t[{len(clients)}]\t{sid}")

# Manejador para el evento 'text'
@sio.event
def text(sid, data):
    print('Mensaje recibido:', data)
    # Envía el mismo mensaje de vuelta al cliente
    sio.emit('text', data, to=sid)

@sio.on('video-start')
def handle_data_start(sid, id, mimetype, total_buffer):
	print(f"Recibiendo video {id} de tipo {mimetype} en fragmentos de {total_buffer} bytes")
	data_transactions[id] = { 'mimetype': mimetype, 'total_buffer': total_buffer, 'chunks': {} }

@sio.on('video-chunk')
def handle_data_chunk(sid, data_uuid, chunk_index, chunk):
	print(f"Recibido fragmento {chunk_index} de {len(chunk)} bytes")

	if data_uuid not in data_transactions:
		print("Error: no se ha recibido el fragmento de inicio")
		return

	# Almacenar cada fragmento en un diccionario con el índice como clave
	data_transactions[data_uuid]['chunks'][chunk_index] = chunk

	# Enviar un ACK al cliente para indicar que el fragmento ha sido recibido
	sio.emit('video-chunk-ack', { 'data_uuid': data_uuid, 'chunk_index': chunk_index})
	sio.emit('text', f"Recibido fragmento {chunk_index} de {len(chunk)} bytes")


	# Si todos los fragmentos han llegado, reconstruir y procesar el video
	if got_all_chunks(data_transactions[data_uuid]['chunks'], data_transactions[data_uuid]['total_buffer']):
		print(f"Todos los fragmentos recibidos, procesando video {data_uuid}")
		video_chunks = data_transactions[data_uuid]['chunks']
		video_completo = ''.join([video_chunks[i] for i in sorted(video_chunks.keys())])
		video_path = f"video_{data_uuid}.{data_transactions[data_uuid]['mimetype'].split('/')[1]}"
		save_data(video_completo, video_path)
		print(f"Video procesado y guardado como {video_path}")
		sio.emit('text', "Video recibido, procesando...")
		infer_text = face_landmarker.infer(data_filename = "media_set/" + video_path)
		print(f"Texto inferido: {infer_text}")
		sio.emit('text', infer_text)

		del data_transactions[data_uuid]
		sio.emit('text', "Video recibido y procesado :D")

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

def save_data(video_base64, filename):
	# Convertir el video de Base64 a bytes
	video_bytes = base64.b64decode(video_base64)

	# crear carpeta 
	if not os.path.exists("media_set/"):
		os.mkdir("media_set/")

	# Guardar el video en un archivo
	with open("media_set/" + filename, "wb") as video_file:
		video_file.write(video_bytes)
    

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

if __name__ == '__main__':
    import eventlet
    eventlet.wsgi.server(eventlet.listen(('', 8080)), app, log_output=False)