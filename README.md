# CVScreener
A simple Python tool to automatically screen and rank resumes based on job descriptions.

## 1. Installation
Clone the repo and install the dependencies:
```bash
git clone [https://github.com/Palomero96/CVScreener.git](https://github.com/Palomero96/CVScreener.git)
cd CVScreener
pip install -r requirements.txt
```
## 2. Setup
- Resumes: Drop your candidate file (PDF) into the resume/ folder.
- Jobs: Open jobs.json and define the position details (keywords, description).
- screener.py: Modify this variables 
    - job_title = "junior_engineer"
    - resume = readPDF("resume/SoftwareEngineer.pdf")

## 3. Run
Execute the script to start screening:
```bash
python screener.py
```

## 4. Results
Check the *evaluation/* folder for the results and rankings.