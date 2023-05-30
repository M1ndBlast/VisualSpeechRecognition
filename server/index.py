# index.js (Comunicacion con el cliente mediante socket.io para recibir y enviar videos)
# Autor: Peduzzi Acevedo Gustavo Alain
# Fecha: 2023-05-25

from aiohttp import web
import base64
import socketio
import openai
import face_landmarker
openai.api_key = "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"

sio = socketio.AsyncServer()
app = web.Application()
sio.attach(app)

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
    print("connect ", sid)
    
@sio.event
def disconnect(sid):
    print('disconnect ', sid)
    
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

		# Detectar rostros
		face_landmarker.landmark_image(filename)

		# Enviar rostros detectados
		with open('landmark.jpg', 'rb') as f:
			# await sio.emit('image', base64.b64encode(f.read()).decode('ascii'))
			await sio.emit('image', base64.b64encode(f.read()).decode('utf-8'))
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
	

if __name__ == '__main__':
	try:
		web.run_app(app)
	except KeyboardInterrupt:
		print('Exiting...')
		exit(0)