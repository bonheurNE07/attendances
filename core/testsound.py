import pyttsx3

# Initialize the TTS engine
engine = pyttsx3.init()

voices = engine.getProperty('voices')
for voice in voices:
    print(f"ID: {voice.id} - Name: {voice.name} - Gender: {voice.gender}")

# Set the voice to a specific ID
engine.setProperty('voice', voices[18].id)  


# Set properties like voice rate (speed) and volume
engine.setProperty('rate', 150)  # Speed of speech
engine.setProperty('volume', 1)  # Volume (0.0 to 1.0)

# Define the text to speak
text_to_speak = "Hello, this is a test of text to speech on a Raspberry Pi."

# Use the TTS engine to speak the text
engine.say(text_to_speak)

# Wait for the speech to complete
engine.runAndWait()
