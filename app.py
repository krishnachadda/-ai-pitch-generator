import os
from dotenv import load_dotenv
from flask import Flask, render_template, request
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
# Configure the Google Gemini API
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    GEMINI_MODEL = 'gemini-1.5-flash-latest' # A fast and capable model
except TypeError:
    print("ERROR: Could not configure Gemini API. Is GEMINI_API_KEY set in your .env file?")
    exit()

# --- Flask App Initialization ---
app = Flask(__name__)

# --- AI Helper Function ---
def generate_pitch_content(idea_bullets):
    """
    Constructs a prompt and queries the Google Gemini API.
    """
    prompt = f"""
    You are an expert startup consultant. Based on the following startup idea, generate a complete business pitch.
    The idea is: "{idea_bullets}"

    Please structure your response clearly with the following sections, using the exact markdown headers:
    
    ## Tagline ##
    (A catchy, memorable one-liner)

    ## Value Proposition ##
    (A clear statement explaining the unique benefit the startup provides)
    
    ## Elevator Pitch ##
    (A compelling 60-second summary of the business)
    
    ## Slide Bullets ##
    (5-7 key bullet points for a pitch deck, covering problem, solution, market, team, and ask)
    
    ## Competitors ##
    (List 2-3 potential direct or indirect competitors)
    
    ## Revenue Models ##
    (Suggest 2-3 possible ways the business could make money, e.g., Subscription, Freemium, Ads)
    """

    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        # This will catch various errors, including authentication and API issues
        print(f"Gemini API request failed: {e}")
        return f"Error: Could not generate content from AI service. The following error occurred: {e}"

def parse_generated_text(text):
    """
    Parses the raw text from the AI into a structured dictionary.
    This function remains largely the same as it relies on the markdown headers.
    """
    # Gemini might not include the prompt, but this split makes the parser robust.
    # It finds the first real header and starts from there.
    if "## Tagline ##" in text:
        clean_text = text.split("## Tagline ##", 1)[1]
    else:
        clean_text = text # Assume the text starts with the tagline content

    sections = {
        'tagline': 'Not found',
        'value_prop': 'Not found',
        'elevator_pitch': 'Not found',
        'slide_bullets': 'Not found',
        'competitors': 'Not found',
        'revenue_models': 'Not found'
    }

    # Split by the known headers
    # We add "Tagline" to the start of the clean text to make the split logic consistent
    parts = ("Tagline ##" + clean_text).split('## ')
    
    for part in parts:
        if part.strip(): # Ensure the part is not empty
            header_and_content = part.split('##', 1)
            header = header_and_content[0].strip().lower().replace(' ', '_')
            content = header_and_content[1].strip() if len(header_and_content) > 1 else ""

            if 'tagline' in header:
                sections['tagline'] = content
            elif 'value_proposition' in header:
                sections['value_prop'] = content
            elif 'elevator_pitch' in header:
                sections['elevator_pitch'] = content
            elif 'slide_bullets' in header:
                sections['slide_bullets'] = content
            elif 'competitors' in header:
                sections['competitors'] = content
            elif 'revenue_models' in header:
                sections['revenue_models'] = content

    return sections

# --- Flask Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    idea = request.form['idea']
    
    # Get raw text from AI
    raw_text = generate_pitch_content(idea)

    if "Error:" in raw_text:
        # Handle API error gracefully
        return render_template('results.html', pitch_data={'error': raw_text})
    
    # Parse the text into a dictionary
    pitch_data = parse_generated_text(raw_text)

    # NO DATABASE - we just send the data straight to the results page
    return render_template('results.html', pitch_data=pitch_data)

# --- Main Execution ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Get port from Render
    app.run(host="0.0.0.0", port=port, debug=True)