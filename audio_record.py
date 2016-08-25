__author__ = "Svarmit"
__version__ = "0.1"
__status__ = "Development"

import pyaudio
import time
import datetime
import numpy as np
import wave
import os
import csv

# Declare variable global so other threads can make use of it
global wavefile, recording

rms_data = []
time_data = []

sample_rate = 44100                 # Sample rate of audio device
frames_per_buffer = 2048            # Number of audio frames delivered per hardware buffer return
channels = 1                        # Number of audio channels (1 = mono)
time_stamp = str(time.time())
fname = time_stamp+ '.wav'   # Output wave filename using current UTC time
total_duration = 1.0                # Total length of wave file
device_id = -1                      # Default audio input device ID
recording = True                    # Boolean check to hold while wait loop
is_mute = 0
wave_status = 1
threshold = 0.07



# Initialize PyAudio
pa = pyaudio.PyAudio()

def select_audio_device():
    """ This method will list all the devices connected to host machine along with its index value"""
    print('Index\tValue\n===============')

    for i in range(pa.get_device_count()):
        devinfo = pa.get_device_info_by_index(i)

        # Convert dictionary key:value pair to a tuple
        for k in list(devinfo.items()):
            name, value = k

            if 'name' in name:
                print i, '\t', value

    try:
        return int(raw_input('\nEnter input device index: '))
    except ValueError:
        print "Not a valid device, falling back to default device"
        return -1

# List and select audio input device
device_id = select_audio_device()
def wave_initialize():
    time_stamp = str(time.time())
    fname = time_stamp + '.wav'
    wave_status = 5
    wavefile = wave.open(fname, 'wb')
    wavefile.setnchannels(channels)
    wavefile.setsampwidth(pa.get_sample_size(pyaudio.paInt16))
    wavefile.setframerate(sample_rate)
    
    return None


def recorder_callback(in_data, frame_count, time_info, status_flags):
    """ This method is called whenever the audio device has acquired the number of audio samples
    defined in 'frames_per_buffer'. This method is called by a different thread to the main thread so some variables
    need to be declared global when altered within it. Avoid any heavy number crunching within this method as it
    can disrupt audio I/O if it blocks for too long.

    Args:
        in_data (str): Byte array of audio data from the audio input device.
        frame_count (int): Number of audio samples/frames received, will be equal to 'frames_per_nuffer'.
        time_info (dict): Dictionary of time information for audio sample data
        status_flags (long): Flag indicating any errors in audio capture
    """
    global recording, rms_data, time_data, wavefile,is_mute,wave_status,fname,time_stamp
    # Convert byte array data into numpy array with a range -1.0 to +1.0

    audio_data = np.fromstring(in_data, dtype=np.int16) / 32767.0

    # Calculate root mean squared of audio buffer
    rms = np.sqrt(np.mean(np.square(audio_data)))

    if rms > threshold:
        is_mute=1
        print rms
        result = rms,time_stamp
        import csv
        with open('rms_timestamp.csv', 'a') as csvfile:
            spamwriter = csv.writer(csvfile, delimiter=',')
            spamwriter.writerow(result)
        wavefile.writeframes(in_data)
        if ((wavefile.getnframes() >= total_duration  * sample_rate)) & (rms<=threshold):
            print 'recording'
            wavefile.close()
    if rms < threshold:
        if wave_status == 5:
            wavefile.writeframes(in_data)
            if ((wavefile.getnframes() >= total_duration  * sample_rate)):
                wavefile.close()
                wave_status=1
                print fname
                if is_mute == 0:
                    os.remove(fname)
                is_mute=0
                time_stamp = str(time.time())
                fname = time_stamp + '.wav'
                wave_status = 5
                wavefile = wave.open(fname, 'wb')
                wavefile.setnchannels(channels)
                wavefile.setsampwidth(pa.get_sample_size(pyaudio.paInt16))
                wavefile.setframerate(sample_rate)


            

    return None, pyaudio.paContinue

# Initialize recording stream object passing all predefined settings
recorder = pa.open(start=False,
                   input_device_index=device_id,
                   format=pyaudio.paInt16,
                   channels=channels,
                   rate=sample_rate,
                   input=True,
                   frames_per_buffer=frames_per_buffer,
                   stream_callback=recorder_callback)

# Open wave file ready for I/O
wavefile = wave.open(fname, 'wb')
wave_status = 5

# Set number of input channels
wavefile.setnchannels(channels)

# Set sample width = 2, as  each 16bit sample value consists of 2 bytes: http://wavefilegem.com/how_wave_files_work.html
wavefile.setsampwidth(pa.get_sample_size(pyaudio.paInt16))

# Set sample rate at 44,100 sample values per second
wavefile.setframerate(sample_rate)

# Start recording stream, triggering hardware buffer fill and callback
recorder.start_stream()

# Hold script in loop waiting for wave file to meet desired file length in seconds
while recording:
    time.sleep(0.1)

# Close all open streams and files
recorder.close()
pa.terminate()