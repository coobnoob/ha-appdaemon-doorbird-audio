import appdaemon.plugins.hass.hassapi as hass
import math
import requests
from requests.exceptions import RequestException
import os
from time import sleep 
from ffmpeg import FFmpeg, Progress, FFmpegError
import subprocess
from io import BytesIO

class DoorbirdException(Exception):
    """An exception for doorbirds"""

class Doorbird:
    def __init__(self, device_ip, username, password):
        """
        Connect to a doorbird 
    
        Args:
            device_ip (str): Doorbird device IP address.
            username (str): Doorbird HTTP username.
            password (str): Doorbird HTTP password.
            
        Raises:
            DoorbirdException     
        """
        self.device_ip = device_ip
        self.username = username
        self.password = password
        
        get_session_url = f"http://{device_ip}/bha-api/getsession.cgi"
        auth = (username, password)
       
        try: 
            response = requests.get(get_session_url, auth=auth)
        except RequestException as exception:
            raise DoorbirdException(exception)
            
        # Check if the request was successful (HTTP status code 200)
        if response.status_code == 200:
            data = response.json()
            self.session_id = data["BHA"]["SESSIONID"]
        else:
            raise DoorbirdException(f"Failed to obtain session ID. Status code: {response.status_code}")
            

    def _generate_audio_chunks(self, output_stream, chunk_size=8*1024):
        """
        Generator function to yield chunks of audio data from a file.
        Doorbird is rate limited to 8K per second
    
        Args:
            output_stream: Stream of audio
            chunk_size (int): Size of each chunk in bytes.
    
        Yields:
            bytes: Chunks of audio data.
        """
        while True:
            chunk = output_stream.read(chunk_size)
            if not chunk:
                break
            sleep(1) # We are rate limiting to chunk_size per second
            yield chunk

    def send_audio(self, audio_file_path):
        """
        Send audio to Doorbird
    
        Args:
            audio_file_path (str): Path to the audio file to be transmitted.
            
        Raises:
            DoorbirdException
        """
        try:
            # Prepare headers
            headers = {
                "Content-Type": "audio/basic",
                "Connection": "Keep-Alive",
                "Cache-Control": "no-cache",
            }
    
            ffmpeg = (
                FFmpeg()
                .option("y")
                .input(audio_file_path)
                .output("pipe:", {"codec:a" : "pcm_mulaw"}, ac=1, ar=8000, f="wav")
            )
             
            result_bytes = ffmpeg.execute()
            
            # Make the POST request with the audio data generator
            audio_transmit_url = f"http://{self.device_ip}/bha-api/audio-transmit.cgi/sessionid={self.session_id}"
            auth = (self.username, self.password)
            with requests.post(
                audio_transmit_url,
                headers=headers,
                data=self._generate_audio_chunks(BytesIO(result_bytes), chunk_size=8*1024),
                auth=auth,
                stream=True,  # Use streaming mode
            ) as response:
                # Check if the request was successful (HTTP status code 200)
                if response.status_code != 200:
                    raise DoorbirdException("Failed to transmit audio. Status code: {response.status_code}")
        except (RequestException, DoorbirdException, FileNotFoundError,FFmpegError) as exception:
            raise DoorbirdException(exception)

#
# Random Light App
#
# Args:
# { probability_from_<on/off>: the likelihood of any one light changing state }
# { max_delay: maximum random delay (in seconds) to toggle }

class DoorbirdAudio(hass.Hass):

  def initialize(self):
     self.listen_event(self.doorbird_audio, "doorbird_audio" )
     

  def doorbird_audio(self, event_name, data, kwargs):
    self.log("------------------------------------------------------------- DoorbirdAudio: %s", event_name )

    print( data )

    try:
      doorbird = Doorbird(data["device_ip"], data["username"], data["password"])
      doorbird.send_audio(data["audio_url"])
    except (DoorbirdException) as exception:
      self.log(f"Failed: {exception}")     
