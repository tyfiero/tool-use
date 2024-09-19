import argparse
import os
from generate_transcripts import generate_transcripts   
from add_videos import add_videos
from process_transcript import process_all_transcripts
from roast import roast_channel

NUMBER_OF_VIDEOS_TO_ADD=5
TEXT_TO_INCLUDE=None
TEXT_TO_EXCLUDE=None
ROAST_CHANNEL_ID= os.environ.get("ROAST_CHANNEL_ID")

def main():
    parser = argparse.ArgumentParser(description="YouTube video processing script")
    parser.add_argument("--roast", action="store_true", help="Enable roast mode")
    parser.add_argument("--discover", nargs='+', help="Search for videos and add them to the playlist")
    parser.add_argument("--include", nargs='+', default=TEXT_TO_INCLUDE, help="Include videos with these words in the title")
    parser.add_argument("--exclude", nargs='+', default=TEXT_TO_EXCLUDE, help="Exclude videos with these words in the title")
    parser.add_argument("--num", type=int, default=NUMBER_OF_VIDEOS_TO_ADD, help="Number of videos to add (default: 5)")

    
    args = parser.parse_args()
    if args.roast:
        print("Roast mode enabled!\n")
        roast_channel(ROAST_CHANNEL_ID)
        return
    elif args.discover:
        query = ' '.join(args.discover)
        print(f"Discovering videos for: {query}")
        print(f"Number of videos to add: {args.num}")
        if args.include:
            print(f"Including text: {args.include[0]}")
        if args.exclude:
            print(f"Excluding text: {args.exclude[0]}")
        add_videos(prompt=query, num_results=args.num, include=args.include[0], exclude=args.exclude[0])
    
    # Generate transcripts for the videos in the playlist
    generate_transcripts()
    
    process_all_transcripts()
        
    print("\n\n🏁 Done!\n\n")
    
if __name__ == "__main__":
    main()