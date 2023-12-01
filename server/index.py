# Autor: Peduzzi Acevedo Gustavo Alain
# Fecha: 2023-05-25

import sys
# caution: path[0] is reserved for script path (or '' in REPL)
sys.path.append('/workspaces/VisualSpeechRecognition/server/vsr') 
sys.path.append('/workspaces/VisualSpeechRecognition/server') 

import os
import time
import base64
import openai
import socketio
import face_landmarker

sio = socketio.Server(always_connect=True, cors_allowed_origins='*', maxHttpBufferSize=1e8)
app = socketio.WSGIApp(sio)

DATA_DIR = 'media_set'
clients = []
data_transactions = {}

@sio.event
def connect(sid, environ):
	clients.append(sid)
	print(f"connect   \t[{len(clients)}]\t{sid}")

@sio.event
def disconnect(sid):
	clients.remove(sid)
	print(f"disconnect\t[{len(clients)}]\t{sid}")

@sio.on('*')
def catch_all(event, sid, data):
	print(f'catch_all  \t{event}\t{sid}\t{data}')

@sio.event
def text(sid, data):
    print('Mensaje recibido:', data)
    sio.emit('text', data, to=sid)

@sio.on('video-start')
def handle_data_start(sid, id, mimetype, total_buffer):
	print(f"Recibiendo video {id} de tipo {mimetype} en fragmentos de {total_buffer} bytes")
	data_transactions[id] = { 'mimetype': mimetype, 'total_buffer': total_buffer, 'chunks': {} }

@sio.on('video-chunk')
def handle_data_chunk(sid, data_uuid, chunk_index, chunk):

	if data_uuid not in data_transactions:
		print("Error: no se ha recibido el fragmento de inicio")
		return

	# Almacenar cada fragmento en un diccionario con el índice como clave
	data_transactions[data_uuid]['chunks'][chunk_index] = chunk

	# Enviar un ACK al cliente para indicar que el fragmento ha sido recibido
	sio.emit('video-chunk-ack', { 'data_uuid': data_uuid, 'chunk_index': chunk_index})

	data = data_transactions[data_uuid]
	print(f"{sum([len(data['chunks'][i]) for i in data['chunks'].keys()])}/{data['total_buffer']}")
	# sio.emit('text', f"{sum([len(data['chunks'][i]) for i in data['chunks'].keys()])}/{data['total_buffer']}")


	# Si todos los fragmentos han llegado, reconstruir y procesar el video
	if got_all_chunks(data_transactions[data_uuid]['chunks'], data_transactions[data_uuid]['total_buffer']):
		print(f"Todos los fragmentos recibidos, procesando: {data_uuid}")
		# sio.emit('data-end-ack', data_uuid)

@sio.on('data-end')
def handle_data_end(sid, data_uuid):
	print(f"Fin de la transacción: {data_uuid}")

	video_chunks = data_transactions[data_uuid]['chunks']
	data_base64 = ''.join([video_chunks[i] for i in sorted(video_chunks.keys())])
	try:
		transaction = data_transactions[data_uuid]
		if transaction['mimetype'] == 'video/mp4':
			process_video(data_uuid, data_base64)

		elif transaction['mimetype'] == 'text/plain':
			process_text(data_uuid, data_base64)
			
	except:
		print("Error en el procesamiento")
		sio.emit('text', "Error en el procesamiento")

	del data_transactions[data_uuid]

def got_all_chunks(chunks, total_buffer):
	if len(chunks) == 0:
		return False
	elif len(chunks) != max(chunks.keys()) + 1:
		return False
	elif sum([len(chunks[i]) for i in chunks.keys()]) != total_buffer:
		return False
	return True

def save_data(video_base64, filename):
	video_bytes = base64.b64decode(video_base64)
	if not os.path.exists(DATA_DIR):
		os.mkdir(DATA_DIR)
	with open(os.path.join(DATA_DIR, filename), 'wb') as video_file:
		video_file.write(video_bytes)
	return os.path.join(DATA_DIR, filename)

def process_video(data_uuid, data_base64):
	video_path = f"video_{data_uuid}.{data_transactions[data_uuid]['mimetype'].split('/')[1]}"
	save_data(data_base64, video_path)

	# temporizador de 10 segundos para simular el procesamiento
	time.sleep(2)

	infer_text = face_landmarker.infer(data_filename = "media_set/" + video_path)
	infer_text = "[TEST] video"
	print(f"Texto inferido: {infer_text}")
	sio.emit('text', infer_text)
	

def process_text(data_uuid, data_base64):
	texto = base64.b64decode(data_base64).decode('utf-8')
	# respuesta = generar_respuesta(data_base64)
	respuesta = "[TEST] texto"
	print(f"Texto recibido: {texto}")
	print(f"Respuesta generada: {respuesta}")
	sio.emit('text', respuesta)

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