# Doorbird Audio
A simple homeassistant AppDaemon app to send audio to a doorbird device.

## Configuration

In your AppDaemon configuration, include ffmpeg in the System packages and python-ffmpeg in the Python packages.

Place the following in your apps.yaml:
```yaml
doorbord_audio:
  module: doorbird_audio
  class: DoorbirdAudio
```
Add doorbird_audio.py to your AddDaemon apps directory.

## Example Usage

Create a home assistant script to raise the "doorbird_audio" event with the device's ip, username, password and a url to the audio of your choice

![image](https://github.com/coobnoob/doorbell-audio/assets/29867612/ed384426-cf60-433b-a9fd-bef0ae2ba7ee)

You can raise this event from whereever you like.


