# Speech Jokey

Speech-Jokey is a speech synthesis application with prosody parametrization for eye-tracking users.

* Main features and objectives
  * Creation of synthesized audio using various speech APIs
  * Optimized for Eye-Tracking users (PwD: Cerbral Palsy,...)
  * Simplified input of prosody parametrization to change parameters like pitch, speaking rate, or emotion of generated audio.

![speech-jokey](https://github.com/HackXIt/assist-heidi-speech-jokey/assets/1595680/b5cd0eb0-2baa-4a0c-b463-ace9526c8def)

## Demo video

[Demo video of the speech jokey program](https://www.youtube.com/watch?v=V3vPxYFN38s) showing the generation of synthetic speech using the Elevenlabs API.

[![Screencast of Speech Jokey showing user interface options and different synthetic voices](https://img.youtube.com/vi/V3vPxYFN38s/0.jpg)](https://www.youtube.com/watch?v=V3vPxYFN38s)

## Install and Run

1. Download and extract the [current release](https://github.com/inclusion-international/speech-jokey/releases).
2. Double-click onto speech-jokey.exe (or the respective command for your OS)

## Developer documentation

Please read the [developer documentation](./doc/developer.md) which describes how to locally install and run the program.

## User documentation

This is what the application currently looks like.

### Main screen
![picture of application](./doc/screenshots/application.png)

### Settings dialog
![picture of application](./doc/screenshots/settings.png)

## Speech Provider

The application currently supports the following speech synthesis provider:
* [ElevenLabs API](https://elevenlabs.io/api)

## Editing the text
To simplify editing the text, the cursor set via eye tracker is always placed at the end of a word. To move the cursor one position to the left or right, the user can use the arrow buttons at the bottom left of the application.

The editing feature is addressed especially to people who need eye tracking devices to move the cursor. 

## Selecting voice
The voice can be selected using the voice selection button or in the settings. All available voices are listed. 
On the selection of a voice a Popup will appear and the selected voice is displayed. 

The currently selected voice is always displayed on the voice selection button.

Using the voice selection button:
![picture of application](./doc/screenshots/select%20voice.png)

## Setting up Speech Provider

To setup a speech provider (e.g. ElevenLabs) the API Key must be entered in the respective settings dialog.
Please check the documenation of your speech provider to get an API key.

![picture of application](./doc/screenshots/settings%20elevenlabs.png)

## Prosody parametrization

Several simplified textual shortcuts can be used to parametrize the prosody of the generated audio.

### Pause

The following punctuation marks can be used to add a speaking pause between words:

* , adds a break of 0.0s
* . adds a break of 0.5s
* ; adds a break of 0.5s

## Synthesizing audio 
An audio file is generated using the synthesizing button. 

![picture of application](./doc/screenshots/synthesize%20confirmation.jpg)

## Playing audio
Before playing the audio file, an audio file has to be synthesized using the synthesizing button.

The file can then be played with the play button.

## Saving the text file 
The final version of the edited text can be saved as a text file.
