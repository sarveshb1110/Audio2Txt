import os
import subprocess
import wave
import string
import azure.cognitiveservices.speech as speechsdk
from docx import Document

def is_compatible_wav(file_path):
    """Check WAV file format compatibility: 16-bit PCM, mono, 16kHz or 8kHz."""
    try:
        with wave.open(file_path, 'rb') as wf:
            return (
                wf.getsampwidth() == 2 and       # 16-bit
                wf.getnchannels() == 1 and       # mono
                wf.getframerate() in (16000, 8000)  # sample rate
            )
    except wave.Error:
        return False

def convert_to_compatible_wav(input_path, output_path):
    """Convert any audio/video to PCM 16-bit mono 16kHz WAV using ffmpeg."""
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-acodec", "pcm_s16le",  # PCM 16-bit Little Endian
        "-ac", "1",              # mono channel
        "-ar", "16000",          # 16kHz sample rate
        output_path
    ]
    subprocess.run(cmd, check=True)
    return output_path

def prepare_wav_for_azure(file_path):
    """Ensure input file is a compatible WAV; convert if needed."""
    ext = os.path.splitext(file_path)[1].lower()
    compatible_wav_path = "converted_for_azure.wav"
    if ext == ".wav" and is_compatible_wav(file_path):
        return file_path
    else:
        return convert_to_compatible_wav(file_path, compatible_wav_path)

def transcribe_audio(audio_path, azure_key, azure_region):
    """Transcribe audio file using Azure Speech SDK."""
    speech_config = speechsdk.SpeechConfig(subscription=azure_key, region=azure_region)
    audio_input = speechsdk.AudioConfig(filename=audio_path)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)
    result = recognizer.recognize_once_async().get()
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text
    else:
        return ""

def postprocess_text(text):
    """Remove punctuation but replace commas and periods with spaced versions."""
    # Remove other punctuation except comma and period
    allowed = {',', '.'}
    cleaned_chars = []
    for ch in text:
        if ch in string.punctuation and ch not in allowed:
            continue
        cleaned_chars.append(ch)
    cleaned_text = ''.join(cleaned_chars)
    # Add space before and after comma and period for readability
    cleaned_text = cleaned_text.replace(',', ' , ').replace('.', ' . ')
    # Normalize multiple spaces
    cleaned_text = ' '.join(cleaned_text.split())
    return cleaned_text

def save_to_word(text, original_file_path):
    """Save the processed text to a Word file with initials of original file."""
    base_name = os.path.splitext(os.path.basename(original_file_path))[0]
    initials = ''.join([word[0] for word in base_name.split()]).upper()
    output_filename = f"{initials}_Transcript.docx"
    doc = Document()
    doc.add_paragraph(text)
    doc.save(output_filename)
    return output_filename

# -------------- Main Flow --------------

def main(file_path, azure_key, azure_region):
    print(f"Preparing audio from file: {file_path}")
    prepared_audio = prepare_wav_for_azure(file_path)

    print("Starting transcription with Azure Speech Service...")
    transcript = transcribe_audio(prepared_audio, azure_key, azure_region)

    if not transcript:
        print("No transcription could be obtained.")
        return

    print("Post-processing transcript...")
    cleaned_text = postprocess_text(transcript)

    print("Saving to Word document...")
    output_file = save_to_word(cleaned_text, file_path)
    print(f"Transcript saved to '{output_file}'")

# ------------------ Usage ------------------

if __name__ == "__main__":
    # Replace with your input file path and Azure Speech Service credentials
    INPUT_FILE = "input_video.mp4"  # example, change as needed
    AZURE_SPEECH_KEY = "YOUR_AZURE_SPEECH_KEY"
    AZURE_SPEECH_REGION = "YOUR_AZURE_SERVICE_REGION"

    main(INPUT_FILE, AZURE_SPEECH_KEY, AZURE_SPEECH_REGION)
