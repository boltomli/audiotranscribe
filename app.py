import os

import azure.cognitiveservices.speech as speechsdk
from aiohttp import web
from ffmpy import FFmpeg

routes = web.RouteTableDef()

@routes.post('/post')
async def handle_post(request):
    reader = await request.multipart()

    field = await reader.next()
    assert field.name == 'audio'
    filename = field.filename

    size = 0
    with open(os.path.join('.', filename), 'wb') as f:
        while True:
            chunk = await field.read_chunk()
            if not chunk:
                break
            size += len(chunk)
            f.write(chunk)
    
    wavefile = filename + '.wav'
    if os.path.exists(wavefile):
        os.remove(wavefile)
    ff = FFmpeg(inputs={filename: None}, outputs={wavefile: '-ac 1'})
    ff.run()

    speech_key, service_region = 'yourkey', 'regionsuchaswestus'
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    audio_config = speechsdk.AudioConfig(filename=wavefile)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    result = speech_recognizer.recognize_once()
    res = 'No response'
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        res = 'Recognized: {}'.format(result.text)
    elif result.reason == speechsdk.ResultReason.NoMatch:
        res = 'No speech could be recognized: {}'.format(result.no_match_details)
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        res = 'Speech Recognition canceled: {}'.format(cancellation_details.reason)
        # if cancellation_details.reason == speechsdk.CancellationReason.Error:
        #     print("Error details: {}".format(cancellation_details.error_details))

    return web.Response(text=res)

app = web.Application()
app.router.add_routes(routes)
web.run_app(app)
