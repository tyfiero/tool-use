from generate_transcripts import get_transcript_from_latest_video
from llm import gemini_response
from process_transcript import process_all_transcripts


def roast_channel(channel_id):
    print("Roasting...")
    get_transcript_from_latest_video(channel_id)
    process_all_transcripts(roast=True)
    