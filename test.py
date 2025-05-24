import ollama

response = ollama.chat(
    model='llama3.2-vision:11b',
    messages=[{
        'role': 'user',
        'content': 'What is in this image?',
        'images': ['/home/binit/Legentia/legal.pdf']
    }]
)

print(response)