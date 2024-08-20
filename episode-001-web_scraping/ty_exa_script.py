import os
import time
import json
import dspy
from dspy.teleprompt import BootstrapFewShot
from exa_py import Exa
from anthropic import Anthropic
from openai import OpenAI
import ollama


LLM_PROVIDER = "anthropic"

# Define the search query
SEARCH_QUERY = "what are the most interesting, and promising AI startups in 2024? Im looking for why the specific company is so great, and what makes it unique"
# Define model to use for Anthropic
ANTHROPIC_CHEAP_MODEL = "claude-3-haiku-20240307"
ANTHROPIC_SOTA_MODEL = "claude-3-5-sonnet-20240620"
OPENAI_SOTA_MODEL = "gpt-4o"
OPENAI_CHEAP_MODEL = "gpt-4o-mini"
OLLAMA_MODEL = "llama3.1"
# Number of results to return from Exa
NUM_EXA_RESULTS = 5

# Configure Exa
exa_api_key = os.getenv("EXA_API_KEY")
exa = Exa(api_key=exa_api_key)
# Initialize Anthropic client
anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
# Configure DSPy 
if LLM_PROVIDER == "openai":
    llm = dspy.OpenAI(model=OPENAI_SOTA_MODEL,  max_tokens=2048, temperature=0.2)
elif LLM_PROVIDER == "anthropic":
    llm = dspy.Claude(model=ANTHROPIC_CHEAP_MODEL, max_tokens=2048, temperature=0.2)
elif LLM_PROVIDER == "ollama":
    llm = dspy.OllamaLocal(model=OLLAMA_MODEL)
dspy.settings.configure(lm=llm)
# Set DSP_CACHEBOOL environment variable to False to disable caching
os.environ['DSP_CACHEBOOL'] = 'False'
os.environ["DSP_CACHEDIR"] = ""





def get_llm_response(prompt, model='cheap'):
    
    if LLM_PROVIDER == "ollama":
        response = ollama.chat(model=OLLAMA_MODEL, messages=[
        {
            'role': 'user',
            'content': prompt,
        },
        ])
        print(response['message']['content'])
    if LLM_PROVIDER == "openai":
        if model == 'cheap':
            model = OPENAI_CHEAP_MODEL
        elif model == 'sota':
            model = OPENAI_SOTA_MODEL
        response = openai_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            max_tokens=2024,
            temperature=0.2,
            stop=None,
        )
        return response.choices[0].message.content
    
    elif LLM_PROVIDER == "anthropic":
        if model == 'cheap':
            model = ANTHROPIC_CHEAP_MODEL
        elif model == 'sota':
            model = ANTHROPIC_SOTA_MODEL
        message = anthropic_client.messages.create(
            max_tokens=2024,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=model,
        )
        
        return message.content[0].text if isinstance(message.content, list) else message.content


# Define the DSPy signature for prompt optimization
class OptimizeUserQuery(dspy.Signature):
    """Based on the user query, enhance the user query to add context, and make it more useful for an AI assistant"""
    user_prompt = dspy.InputField()
    optimized_prompt = dspy.OutputField()

# Create a DSPy module to optimize the prompt
class UserQueryOptimizer(dspy.Module):
    def __init__(self):
        super().__init__()
        self.optimize = dspy.ChainOfThought(OptimizeUserQuery)

    def forward(self, user_prompt):
        optimized = self.optimize(user_prompt=user_prompt)
        return optimized.optimized_prompt
    
    
def run_dspy_user_query_optimizer(user_prompt):
    
    # Create an instance of the UserQueryOptimizer class
    user_query_optimizer = UserQueryOptimizer()
    
    # Call the forward method of the UserQueryOptimizer class with the search_query and summary_prompt as arguments
    optimized_prompt = user_query_optimizer(user_prompt)

    print(f"\n\n👤 \033[94mOptimized user query prompt from DSPy:\n\n {optimized_prompt}\033[0m\n\n ")
    return optimized_prompt




# Define the DSPy signature for prompt optimization
class OptimizePrompt(dspy.Signature):
    """Based on the user query, generate a summary prompt to create a useful prompt for an AI assistant that will summarize a website. The summary prompt should be formatted in a way that it can be used as an input to the AI assistant, and should be themed around the user query. The summary prompt should be formatted as a single string, with no line breaks or other formatting. The summary prompt should be at least 5-7 sentences long, but no more than 8 sentences. Remember, this should be a prompt for an AI assistant, write in in the format of a LLM prompt.  IMPORTANT: Do NOT talk about the website, only the contents of the website.  Only include information about the content of the website, avoid language like: "This article..." or "This page..."""
    user_prompt = dspy.InputField()
    optimized_prompt = dspy.OutputField()

# Create a DSPy module to optimize the prompt
class SummaryPromptOptimizer(dspy.Module):
    def __init__(self):
        super().__init__()
        self.optimize = dspy.ChainOfThought(OptimizePrompt)

    def forward(self, user_prompt):
        optimized = self.optimize(user_prompt=user_prompt)
        return dspy.Prediction(optimized_prompt=optimized.optimized_prompt)




def run_dspy_summarizer_prompt_optimizer(user_prompt):
    
    # Create a list of examples of great summarizer prompts
    examples = [
        dspy.Example(
            user_prompt="What are the most interesting AI startups? What makes them great startups?",
            optimized_prompt= """Summarize the website to get the general idea of what the company does, summarize it in a format to highlight how unique the startup is. Basically an elevator pitch. Something like: \"Paradox AI - the AI assistant for recruiting. Paradox makes it easy to find great candidates using the power of AI. It works by ....\" and so on. At the end of the response, showcase WHY this idea is important. And why it would make a great startup from both the innovation and business standpoint. Ideally 5-7 sentences. Only include information about the content of the website, avoid language like: "This article..." or "This page..."""
        ).with_inputs("user_prompt"),
        dspy.Example(
            user_prompt="What are some of the best traditional apple pie recipes that are beginner-friendly and include cinnamon and Granny Smith apples?",
            optimized_prompt= "Summarize the website that features beginner-friendly traditional apple pie recipes, specifically those that include cinnamon and Granny Smith apples. Focus on the simplicity of the instructions and the common ingredients that make these recipes accessible for novice bakers. Highlight the importance of flavor balance and texture in creating a delicious apple pie. Include tips for preparation and baking that can help beginners achieve the best results. Provide a list of recommended toppings and variations to add to the pie. The summary should be at least 5-7 sentences long, but no more than 8 sentences. Only include information about the content of the website, avoid talking about how the information is on a website\""
        ).with_inputs("user_prompt"),
    ]
    
    # Create an instance of the SummaryPromptOptimizer class
    summary_prompt_optimizer = SummaryPromptOptimizer()
    
    # Create a teleprompter (optimizer) instance
    teleprompter = BootstrapFewShot(metric=lambda example, pred, trace=None: True)
    
    # Compile the teleprompter with the summary_prompt_optimizer and the examples
    compiled_optimizer = teleprompter.compile(summary_prompt_optimizer, trainset=examples)

    # Call the forward method of the SummaryPromptOptimizer class with the user_prompt as argument
    result = compiled_optimizer(user_prompt=user_prompt)

    # Get the optimized prompt from the result
    optimized_prompt = result.optimized_prompt

    print(f"\n\n 📝 \033[94mOptimized summarizer prompt from DSPy:\n\n {optimized_prompt}\033[0m\n\n")
    return optimized_prompt




def get_exa_responses(search_query, summary_prompt):
    result = exa.search_and_contents(
        search_query,
        type="neural",
        use_autoprompt=True,
        num_results=NUM_EXA_RESULTS,
        summary={
            "query": summary_prompt
        }
    )
    
    return result.results



def generate_training_data(exa_responses):
    try:
        all_data = []
        for i, response in enumerate(exa_responses, 1):
            ai_assistant_result = response.summary
            likely_user_query = get_llm_response(prompt=f"""
                Given the following result from an AI assistant, provide ONE example of what user query was likely used to get this result. Respond ONLY with the user query.
                
                AI Assistant Result: {ai_assistant_result}                    
            """, model="cheap")
            
            
            all_data.append({
                "user": likely_user_query,
                "assistant": ai_assistant_result
            })
            
            # Pretty print the results
            print(f"\n🔎 \033[95mExa Response {i}:\n{response.summary.strip()}\033[0m\n")
            print(f"\n🤖 \033[92mGenerated likely user query:\n {likely_user_query}\033[0m\n")

            print("-" * 50)  # Separator between responses
        if len(all_data) == 0:
                print("No data found, please try again with more exa responses")
                return
        n = 3
        if len(all_data) < 3:
            n = len(all_data)

        first_n_data = all_data[:n]
        
        formatted_data = "\n".join([f"User: {item['user']}\nAssistant: {item['assistant']}\n" for item in first_n_data])

        sys_prompt_gen_prompt = f"""
            Given the conversation between a user and an AI assistant below, create a system prompt that was most likely used to get the assistant's response. The system prompt should be formatted in a way that it can be used as an input to the AI assistant, and should be themed around the user query. Remember: system prompts are usually fairly general, and not specific. The system prompt should be formatted as a single string, with no line breaks or other formatting. The system prompt should be between 1-3 sentences long. Provide your response in valid JSON format, like this: {{"prompt": "YOUR_PROMPT_HERE"}}. Do NOT provide any other information.
            
            Conversation:
            {formatted_data}
            """
            
        # Generate the system prompt using Anthropic's API, but lets make sure it's valid JSON and has a 'prompt' key
        max_attempts = 4
        for attempt in range(max_attempts):
            try:
                generated_system_prompt = get_llm_response(prompt=sys_prompt_gen_prompt, model="sota")
                generated_system_prompt = json.loads(generated_system_prompt)
                
                if "prompt" in generated_system_prompt:
                    generated_system_prompt = generated_system_prompt["prompt"]
                    break  # If successful, exit the loop
                else:
                    print("Error: Generated system prompt is not valid JSON, trying again...")
                    continue
                
            except:
                if attempt < max_attempts - 1:  # If not the last attempt
                    print(f"Attempt {attempt + 1} failed: Generated system prompt is not valid JSON, trying again...")
                else:
                    print(f"Error: Failed to generate valid JSON after {max_attempts} attempts.")
                    raise  # Re-raise the last exception if all attempts fail
        
        print(f"\n👽 \033[96mGenerated likely system prompt:\n {generated_system_prompt}\033[0m\n")
        
        
        # Generate a jsonl file with the required format, save it to the downloads folder
        downloads_folder = os.path.expanduser("~/Downloads")
        # Add a timestamp to the file name
        current_time = time.strftime("%m-%d-%Y-%H:%M")
        file_name = f"training_data_{current_time}.jsonl"
        file_path = os.path.join(downloads_folder, file_name)
        
        with open(file_path, "w") as f:
            for item in all_data:
                entry = {
                    "messages": [
                        {"role": "system", "content": generated_system_prompt},
                        {"role": "user", "content": item["user"]},
                        {"role": "assistant", "content": item["assistant"]}
                    ]
                }
                f.write(json.dumps(entry) + "\n")

        print(f"\n\n📝 \033[38;5;218mGenerated training data saved to {file_path}\033[0m\n\n")
    except Exception as e:
        print(f"\n\n❌ Error making training data: {str(e)}")
        return

if __name__ == "__main__":
    try:
        start_time = time.time()
        
        # Run DSPy to optimize the user query
        optimized_user_query = run_dspy_user_query_optimizer(user_prompt=SEARCH_QUERY)
        
        # Run DSPy to optimize the summary prompt
        optimized_summary_prompt = run_dspy_summarizer_prompt_optimizer(user_prompt=optimized_user_query)
        
        # Run Exa to get the results
        exa_responses = get_exa_responses(search_query=optimized_user_query, summary_prompt=optimized_summary_prompt)
        
        print("\n\n🔎 Exa responses:\n")
        
        # Generate training data
        generate_training_data(exa_responses)
        
        # Log the time taken
        end_time = time.time()
        print(f"\n\n🏁 Total time taken: {end_time - start_time:.2f} seconds\n\n\n\n\n")
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
