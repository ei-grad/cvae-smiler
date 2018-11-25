import logging
from functools import wraps
from io import BytesIO

import numpy as np

from keras import backend as K

def vae_loss(y_true, y_pred):
    recon = K.sum(K.binary_crossentropy(K.flatten(y_true), K.flatten(y_pred)), axis=-1)
    kl = 0.5 * K.sum(K.exp(l_sigma) + K.square(mu) - 1. - l_sigma, axis=-1)
    return recon + kl


import keras.losses
keras.losses.vae_loss = vae_loss

from keras.models import load_model

from PIL import Image

from emoji import emojize

import requests

from bottle import Bottle, run, request, abort

from settings import BOT_TOKEN, WEBHOOK_TOKEN


app = Bottle()

logging.basicConfig(level=logging.DEBUG)



def send_request(method, files=None, **kwargs):
    return requests.post('https://api.telegram.org/bot%s/%s' % (
        BOT_TOKEN, method
    ), files=None, data=kwargs).json()


def handle_errors(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception:
            logging.error("Failed processing %r", request.body, exc_info=True)
            abort(400)
    return f


#model = load_model('model.h5')


@app.route('/<token>', method='POST')
@handle_errors
def botapi(token):

    if token != WEBHOOK_TOKEN:
        raise abort(404)

    update = request.json
    logging.info("Got update: %r", update)

    if 'message' in update:
            msg = update['message']
            if 'photo' not in msg:
                return {
                    'method': 'sendMessage',
                    'chat_id': msg['chat']['id'],
                    'text': 'Бот принимает только фотографии.',
                }
            r = send_request('getFile', file_id=msg['photo'][0]['file_id'])
            print(r)
            r = requests.get('https://api.telegram.org/file/bot%s/%s' % (BOT_TOKEN, r['result']['file_path']))
            logging.info('Response for sendPhoto: %s', send_request('sendPhoto',
                                                                     chat_id=msg['chat']['id'],
                                                                     photo=msg['photo'][0]['file_id']))
            #print("Response: %s\nImage: %r" % (r, r.content[:50]))
            #img = Image.open(BytesIO(r.content))  # noqa
            #logging.info('Photo %s downloaded!', img.size)

            #buf = BytesIO()
            #img = model.predict([[img], [1]])
            #img = Image.fromarray((img * 255).astype(np.uint8))
            #img.save(buf, "jpeg")
            #send_request('sendPhoto', files={'file': ('photo.jpg', buf, 'image/jpeg', {'Expires': '0'})})

            return {
                'method': 'sendMessage',
                'chat_id': msg['chat']['id'],
                'text': 'Ok',
            }
    else:
        logging.error("Unsupported update: %s", update)
        return {
            'method': 'sendMessage',
            'chat_id': msg['chat']['id'],
            'text': emojize('бот не понимает сообщения такого типа :confused:'),
        }


if __name__ == "__main__":
    run(app, host='0.0.0.0', port=8000)
