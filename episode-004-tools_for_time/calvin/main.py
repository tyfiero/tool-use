from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich import box
from llm import llm

console = Console()

def main():
    conversation_history = []
    
    print(f"""
          
          
  ___|       |       _)       
 |      _` | |\ \   / | __ \  
 |     (   | | \ \ /  | |   | 
\____|\__,_|_|  \_/  _|_|  _| 
                              
          """)
    
    console.print(Panel.fit("🗓️ [bold cyan]Hi! I'm Calvin, your AI Calendar Assistant! What can I help you with today?[/bold cyan] 🤖", border_style="bold green"))
    
    while True:
        user_input = Prompt.ask("\n[bold yellow]You[/bold yellow]")
        if user_input.lower() == 'quit':
            console.print(Panel.fit("[bold red]Goodbye! Have a great day! 👋[/bold red]", border_style="bold red"))
            break
        
        conversation_history.append({"role": "user", "content": user_input})
        
        console.print("\n[bold green]Thinking...[/bold green]")
        response = llm(conversation_history)
        
        conversation_history.append({"role": "assistant", "content": response})
        
        md = Markdown(response)
        console.print(Panel(md, title="[bold cyan]AI Assistant[/bold cyan]", border_style="cyan", box=box.ROUNDED))

if __name__ == '__main__':
    main()