import os
import dspy
import json
import shutil
from datetime import datetime
from dsp.modules import GoogleVertexAI  
from google.oauth2 import service_account
os.environ['GRPC_VERBOSITY'] = 'error'
from llm import gemini_response

# llm = dspy.OllamaLocal(model="llama3.1")
# dspy.configure(lm=llm)

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

output_env = os.getenv("OUTPUT_DIR")
output_dir = os.path.expanduser(output_env)

unprocessed_dir = os.path.join(base_dir, "experiments", "youtube", "transcripts", "unprocessed")

processed_dir = os.path.join(base_dir,  "experiments", "youtube","transcripts", "processed")
        

def process_all_transcripts(roast=False):
    try:
        print("\n\n📝 Processing transcripts...\n")
        # configure and authenticate the vertex ai model for DSPy
        credentials_path = os.path.join(os.getcwd(), "service_account_secret.json")
        credentials = service_account.Credentials.from_service_account_file(credentials_path)
        vertex_ai = GoogleVertexAI(
            model_name="gemini-1.5-flash-001",
            project="booming-octane-433204-v6",
            location="us-central1",
            credentials=credentials
        )
        dspy.configure(lm=vertex_ai)
        
        
        

        os.makedirs(processed_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        for filename in os.listdir(unprocessed_dir):
            print(f"📄 Processing {filename}")
            if filename.endswith(".json"):
                file_path = os.path.join(unprocessed_dir, filename)
                
                with open(file_path, 'r') as file:
                    video_data = json.load(file)
                
                if roast:
                    markdown_content = roast_transcript(video_data)

                else:
                    summary = process_transcript(
                        video_data['transcript'],
                        video_data['title'],
                        video_data['description']
                    )

                    markdown_content = create_markdown_with_frontmatter(summary, video_data)
                    

                # Create markdown filename
                md_filename = video_data['title'][:100]  # Limit length to first 100 characters
                md_filename = ''.join(c if c.isalnum() or c in [' ', '-', '_'] else '_' for c in md_filename)
                md_filename = md_filename.strip() + ".md"
                md_file_path = os.path.join(output_dir, md_filename)
                
                print(f"\n📝 Writing md to {md_file_path}")
                with open(md_file_path, 'w') as md_file:
                    md_file.write(markdown_content)
                    
                    
                # Move processed JSON file
                shutil.move(file_path, os.path.join(processed_dir, filename))

                print(f"✅Processed: {filename}\n")
    except Exception as e:
        print(f"🚨 Error processing files: {e}")
            
def process_transcript(transcript, title, description):
    print(f"\nProcessing transcript for {title}\n")
    summarizer = YouTubeSummarizer()
    
    result = summarizer(title=title, description=description)
    print(f"🤖 Generated summary prompt: {result.summarization_prompt}")
    
    # Generate a summary from the summarization prompt
    summary = gemini_response(result.summarization_prompt, temp=0.5)
    print(f"\nSummary: {summary[:50]}...")
    # Use the summary to extract the key takeaways
    key_takeaways = gemini_response(f""",Given a summary of a video transcript, extract the key takeaways in markdown bullet point format. The key takeaways are the most important points that someone should care about. They should ideally be actionable, interesting, or useful. Aim for 3-12 key takeaways.
                                    
    Summary:                        
    {summary}""", temp=0.5)
    print(f"\nKey takeaways: {key_takeaways[:50]}...")
    
    # Use the key takeaways to select the most important one
    one_key_takeaway = gemini_response(f"""Of the following key takeaways of a video transcript, select the most actionable, interesting, or useful one. The one takeaway that someone really should care about. You can repeat it exactly, or rephrase it in a way that makes it more actionable and interesting.
    
    Key takeaways:                          
    {key_takeaways}""", temp=1)
    
    print(f"\nOne key takeaway: {one_key_takeaway[:50]}...")
    
    # Use the summary and key takeaways to create a TLDR
    tldr = gemini_response(f"""What's the TLDR from the following summary of video transcript? Why should someone care about it? What, in one to two sentences, is this summary in a nutshell? 
    
    Summary:                           
    {summary}""", temp=0.5)
    
    print(f"\nTLDR: {tldr[:50]}...")
    
    
    md_data = f"""
{"## TLDR" if not tldr.lower().startswith("tldr") else ""}
{tldr}

## Most useful takeaway
**{one_key_takeaway}**

## All key takeaways
{key_takeaways}

## Summary
{summary}
        
## Transcript
{transcript}
    """
    
    return md_data


def create_markdown_with_frontmatter(summary, video_data):
    frontmatter = f"""---
title: "{video_data['title']}"
channel_name: "{video_data['channel_name']}"
view_count: "{video_data['view_count']}"
publish_date: "{video_data['publish_date']}"
processed_date: "{datetime.now().isoformat()}"
description: "{video_data['description']}"
---

## {video_data['channel_name']}
Published: {datetime.fromisoformat(video_data['publish_date']).strftime('%B %d, %Y')}, Processed: {datetime.now().strftime('%B %d, %Y')}

[![Thumbnail]({video_data['thumbnail']})]({video_data['video_url']})

{summary}
"""
    return frontmatter


class SummarizationPromptGenerator(dspy.Signature):
    """Given the title and description of a YouTube video, generate a summarization prompt to be used with an AI assistant. The prompt should be specific to the video title and description, and aim to provide an engaging and informative summary of the video's content. Make the prompt in a way that is easy to understand and follow, and avoid using technical jargon or complex language, and remember that the general idea here is to make a prompt so that the AI can create the best possible summary of the video, packed with key takeaways and useful insights."""
    title = dspy.InputField()
    description = dspy.InputField()
    summarization_prompt = dspy.OutputField()

    
    
class YouTubeSummarizer(dspy.Module):
    def __init__(self):
        super().__init__()
        self.summarization_prompt_generator = dspy.ChainOfThought(SummarizationPromptGenerator)

    def forward(self, title, description):
        # Create a summarization prompt
        summarization_prompt = self.summarization_prompt_generator(title=title, description=description)
        
        return dspy.Prediction(summarization_prompt=summarization_prompt.summarization_prompt)
    
    
    
    

def roast_transcript(video_data):
    
    useful_video_data = f"""
    Video views: {video_data["view_count"]}
    Likes: {video_data["like_count"]}
    Comments: {video_data["comment_count"]}
    Duration: {video_data["duration"]}
    Transcript:
    {video_data["transcript"]} """
    
    constructive = gemini_response(f"""You are a professional YouTuber and esteemed podcast host. Two aspiring podcasters have given you a podcast transcript from their latest episode: {video_data["title"]}, you have been tasked with giving constructive feedback. They are seeking actionable advice on how to improve the podcast. From growth tips like YouTube SEO, to delivery and content, nothing is off the table. What went well, what could improve, they want any and all feedback to improve their skills and final product. Format all responses as markdown, and remember to to be constructive and positive!

    {useful_video_data}
   """, temp=0.5)
    print(f"\nConstructive feedback: {constructive[:50]}...")


    # ROAST 'EM!!!
    roast = gemini_response(f"""You're a witty comedian at a roast battle. Two aspiring podcasters have given you a podcast transcript from their latest episode: {video_data["title"]}, your job is to roast them. Comedy central style. Don't be afraid to give 'em a good ROAST!
    
    Remember to:
    1. Keep it clever and creative - puns and wordplay are your friends.
    2. Focus on their content and delivery, not personal attacks.
    3. Mix in some backhanded compliments for extra laughs.
    4. Reference specific moments or quotes from the transcript if possible.
    5. End with a light-hearted encouragement to keep improving.

    Use this info to fuel your roast:
    {useful_video_data}""", temp=1)
    print(f"\nRoast: {roast[:50]}...")
    
    
    
    
    md_data = f"""
## {video_data['channel_name']}
### Views: {video_data["view_count"]}
### Likes: {video_data["like_count"]}
### Comments: {video_data["comment_count"]}
### Duration: {video_data["duration"]}
Published: {datetime.fromisoformat(video_data['publish_date']).strftime('%B %d, %Y')}, Processed: {datetime.now().strftime('%B %d, %Y')}

[![Thumbnail]({video_data['thumbnail']})]({video_data['video_url']})
        
## Constructive Feedback
{constructive}
        
## ROAST 🔥
{roast}
    """
    return md_data