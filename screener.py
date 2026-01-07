
import os
from pypdf import PdfReader
import json
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

# Cargamos las variables de entorno
from dotenv import load_dotenv
load_dotenv()  # Carga .env

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def readPDF(resumePath):
    """
    Extract text from pdf file.
    
    Args:

    Returns:
        text : Extracted text from pdf
    """
    if not os.path.exists(resumePath):
        print(f"Error: The file '{resumePath}' was not found.")
        print("Please check the file name and directory.")
        
    else:
        try:
            reader = PdfReader(resumePath)
            text = ""
        
            for page in reader.pages:
                text += page.extract_text()
                
            print("Success: Resume loaded successfully.")
            # print(text) # Optional: print to check content
            return text

        except Exception as e:
            print(f"Error: Could not read the PDF. Details: {e}")


def load_job_description(job_key, jobsPath='jobs.json'):
    """
    Load specific job description from JSON file.
    
    Args:
        job_key: Selected Job to load
        file_path: Path to JSON file

    Returns:
        dict : Selected job description
    """
    if not os.path.exists(jobsPath):
        print(f"Error: The file '{jobsPath}' was not found.")
        return None

    try:
        # Load JSON
        with open(jobsPath, 'r', encoding='utf-8') as f:
            all_jobs = json.load(f)

        # Get Specific item 
        job_data = all_jobs.get(job_key)
        if not job_data:
            print(f"Error: Job key '{job_key}' not found in the file.")
            return None
        return job_data
    
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON. Check '{jobsPath}' for formatting errors.")
        return None

def clean_and_parse_json(llm_output_str):
    """
    Removes markdown formatting (```json) and converts string to dict.
    
    Args:
        llm_output_str: llm response
    
    Returns:
        dict : Json formatted file
    """
   
    # Remove the markdown code block indicators
    clean_text = llm_output_str.replace("```json", "").replace("```", "").strip()

    try:
        # Convert string to Python Dictionary
        return json.loads(clean_text)
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")
        return None
    
def save_candidate_to_db(candidate_data, filename):
    """
    Appends a candidate to the JSON file only if they don't already exist.
    
    Args:
        candidate_data: Information about candidated evauated by llm
        filename: Json file with all candidates
    
    """
    candidates = []
    pathtofile = "evaluation/"+ filename + ".json"
    print(pathtofile)
    # Load existing data
    if os.path.exists(pathtofile):
        try:
            with open(pathtofile, 'r', encoding='utf-8') as f:
                content = f.read()
                if content:
                    candidates = json.loads(content)
        except json.JSONDecodeError:
            candidates = [] # Start fresh if file is corrupted

    # Check for duplicates (by name)
    new_name = candidate_data.get("candidate_name", "Unknown")
    
    if any(c.get("candidate_name") == new_name for c in candidates):
        print(f"Skipping: Candidate '{new_name}' already exists in {pathtofile}.")
        return

    # Append and Save
    candidates.append(candidate_data)

    try:
        with open(pathtofile, 'w', encoding='utf-8') as f:
            json.dump(candidates, f, indent=4, ensure_ascii=False)
        print(f"Success: Saved '{new_name}' to '{pathtofile}'")
        
    except Exception as e:
        print(f"Error saving file: {e}")

class ScreenerLLM:
    """
    LLM class definition used for analyzing candidate suitability.

    Attributes:
        llm (ChatGoogleGenerativeAI): The configured Gemini client instance acting 
            as the reasoning engine (model version, temperature, api_key).
        prompt (PromptTemplate): The instruction template that defines the 
            'Expert Recruiter' persona, evaluation criteria, and forced JSON output format.
    """
    def __init__(self):
        # Google Gemini API
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.0,
            google_api_key=GEMINI_API_KEY
        )
        

        # PROMPT 
        self.prompt = PromptTemplate.from_template("""
                You are an expert Technical Recruiter and Hiring Manager with 20 years of experience. 
                Your task is to objectively evaluate a candidate's resume against a provided job description.

                Input Data:
                1. Job Description (JSON/Text format): {job_description}
                2. Candidate Resume (Text format): {resume}

                Instructions:
                1. Analyze the correlation between the Job Description requirements (skills, tech stack, experience) and the Candidate's Resume.
                2. Look for evidence of specific skills, not just keyword matching. Context matters.
                3. Be critical. If a required skill is missing, note it.
                4. Calculate a compatibility score from 0 to 100.

                Output Format:
                You must return ONLY a valid JSON object. Do not add any conversational text, markdown formatting (like ```json), or explanations outside the JSON.

                The JSON structure must be:
                {{
                    "candidate_name": "Name extracted from resume or 'Unknown'",
                    "compatibility_score": <int 0-100>,
                    "summary": "A brief 2-3 sentence executive summary of the candidate.",
                    "strengths": ["List of 3-5 key matching skills or experiences"],
                    "missing_critical_skills": ["List of mandatory skills from JD not found in resume"],
                    "experience_level_assessment": "Junior, Mid, Senior, or Mismatch",
                    "recommendation": "Interview", "Hold", or "Reject"
                }}
                                                   
            """)
    def evaluate_candidate(self,  state: dict) -> dict:
        """
        Performs a semantic evaluation of the candidate's resume against the job description using the configured LLM.
        
        Args:
            self: The instance of the ScreenerLLM class (provides access to self.llm and self.prompt).
            state (dict): The current graph state containing the keys 'job_description' and 'resume'.
        
        Returns:
            dict: The updated state dictionary, including the original data plus a new 'output' key containing the LLM's analysis (AIMessage).
        """    
        prompt_text = self.prompt.format(job_description=state['job_description'], resume=state['resume'])
        # Run LLM with defined prompt text
        response = self.llm.invoke(prompt_text)
        # Merge existing state with the new LLM output
        return {**state, "output": response}

if __name__ == "__main__":
    job_title = "junior_engineer"
    resume = readPDF("resume/SoftwareEngineer.pdf")
    job_description = load_job_description(job_title)
    screneer = ScreenerLLM()
    inputs = {
            "resume": resume,
            "job_description":job_description,
            "output": ""
        }
    
    output = screneer.evaluate_candidate(inputs)
    json_result = output['output'].content
    
    canditate = clean_and_parse_json(json_result)

    save_candidate_to_db(canditate,job_title)
    #print(canditate)
    
