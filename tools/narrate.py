"""Generate WAV narration through installed Windows SAPI, without changing policies."""
import json
from pathlib import Path
import comtypes.client
from demo_chapters import CHAPTERS
root=Path(__file__).resolve().parents[1]
folder=root/'.tools/demo'
folder.mkdir(parents=True,exist_ok=True)
chapters=CHAPTERS
(folder/'chapters.json').write_text(json.dumps(chapters,indent=2),encoding='utf-8')
print('Initializing installed Windows speech voice',flush=True)
voice=comtypes.client.CreateObject('SAPI.SpVoice',dynamic=True)
voices=voice.GetVoices()
for i in range(voices.Count):
    token=voices.Item(i)
    if 'Zira' in token.GetDescription():voice.Voice=token;break
voice.Rate=0
for chapter in chapters:
    print('Synthesizing '+chapter['key'],flush=True)
    stream=comtypes.client.CreateObject('SAPI.SpFileStream',dynamic=True)
    audio_format=comtypes.client.CreateObject('SAPI.SpAudioFormat',dynamic=True)
    audio_format.Type=22
    stream.Format=audio_format
    stream.Open(str(folder/(chapter['key']+'.wav')),3,False)
    voice.AudioOutputStream=stream
    voice.Speak(chapter['narration'],0)
    stream.Close()
print('Narration files complete',flush=True)
