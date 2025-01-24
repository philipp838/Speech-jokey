#!/usr/bin/env python3
"""Play an audio file using a limited amount of memory.

This is the same as play_long_file.py, but implemented without using NumPy.

"""
import argparse
import logging
import queue
import sys
import threading

import sounddevice as sd
import soundfile as sf

class SDPlayback:
    buffersize = 20
    blocksize = 2048

    def __init__(self, filename, device=0):
        self.q = queue.Queue(maxsize=self.buffersize)
        self.event = threading.Event()

        self.filename = filename
        self.device = device
        logging.info(f"file: {filename}, device: {device}")

    def callback(self, outdata, frames, time, status):
        assert frames == self.blocksize
        if status.output_underflow:
            print('Output underflow: increase blocksize?', file=sys.stderr)
            raise sd.CallbackAbort
        assert not status
        try:
            data = self.q.get_nowait()
        except queue.Empty as e:
            print('Buffer is empty: increase buffersize?', file=sys.stderr)
            raise sd.CallbackAbort from e
        if len(data) < len(outdata):
            outdata[:len(data)] = data
            outdata[len(data):] = b'\x00' * (len(outdata) - len(data))
            raise sd.CallbackStop
        else:
            outdata[:] = data


    def play(self):
        try:
            with sf.SoundFile(self.filename) as f:
                logging.info(f"file: {self.filename}, samplerate: {f.samplerate}, channels: {f.channels}, format: {f.format}, subtype: {f.subtype}, device: {self.device}")
                for _ in range(self.buffersize):
                    data = f.buffer_read(self.blocksize, dtype='float32')
                    if not data:
                        break
                    self.q.put_nowait(data)  # Pre-fill queue
                stream = sd.RawOutputStream(
                    samplerate=f.samplerate, blocksize=self.blocksize,
                    device=self.device, channels=f.channels, dtype='float32',
                    callback=self.callback, finished_callback=self.event.set)
                with stream:
                    timeout = self.blocksize * self.buffersize / f.samplerate
                    while data:
                        data = f.buffer_read(self.blocksize, dtype='float32')
                        self.q.put(data, timeout=timeout)
                    self.event.wait()  # Wait until playback is finished
        except KeyboardInterrupt:
            logging.error('\nInterrupted by user')
        except queue.Full:
            # A timeout occurred, i.e. there was an error in the callback
            logging.error('Queue full')
        except Exception as e:
            print(f"exception: {type(e)}")


if __name__ == '__main__':
    def int_or_str(text):
        """Helper function for argument parsing."""
        try:
            return int(text)
        except ValueError:
            return text


    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        '-l', '--list-devices', action='store_true',
        help='show list of audio devices and exit')
    args, remaining = parser.parse_known_args()
    if args.list_devices:
        print(sd.query_devices())
        parser.exit(0)
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[parser])
    parser.add_argument(
        'filename', metavar='FILENAME',
        help='audio file to be played back')
    parser.add_argument(
        '-d', '--device', type=int_or_str,
        help='output device (numeric ID or substring)')
    parser.add_argument(
        '-b', '--blocksize', type=int, default=2048,
        help='block size (default: %(default)s)')
    parser.add_argument(
        '-q', '--buffersize', type=int, default=20,
        help='number of blocks used for buffering (default: %(default)s)')
    args = parser.parse_args(remaining)
    if args.blocksize == 0:
        parser.error('blocksize must not be zero')
    if args.buffersize < 1:
        parser.error('buffersize must be at least 1')

    print(f"file: {args.filename}, device: {args.device}, current: {__file__}")
    sdplay=SDPlayback(filename=args.filename,device=args.device)
    sdplay.play()

    #data, fs = sf.read(args.filename)
    #sd.play(data, fs)
    #sd.wait()