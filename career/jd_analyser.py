from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv(r"C:\Dev\.env")

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def analyse_job_description(jd_text):
    prompt = f"""
You are ARIA, an expert AI career assistant.
Analyse the job description below and respond in EXACTLY this format — no extra text:

JOB TITLE: [job title here]
COMPANY: [company name here]
LOCATION: [location here]
EXPERIENCE REQUIRED: [years here]
LEVEL: [Entry / Mid / Senior]

REQUIRED SKILLS:
- [skill 1]
- [skill 2]
- [add all skills found]

KEY RESPONSIBILITIES:
- [responsibility 1]
- [responsibility 2]
- [add all found]

SUMMARY:
[One clear sentence describing what this role is about]

MATCH TIPS:
[Two sentences on what a candidate should highlight to get this role]

Job Description:
{jd_text}
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are ARIA, an AI career assistant. Always respond in the exact format requested."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content


def read_jd_from_file(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return None
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
    return content


def analyse_skill_gap(jd_analysis, candidate_skills):
    prompt = f"""
You are ARIA, an expert AI career assistant.
Compare the candidate's skills against the job requirements.
Respond in EXACTLY this format — no extra text:

MATCHING SKILLS:
- [skills candidate has that match the job]

MISSING SKILLS:
- [skills required by job that candidate does not have]

PRIORITY LEARNING ORDER:
1. [most important missing skill] — [why] — [estimated weeks to learn basics]
2. [second most important] — [why] — [estimated weeks]
3. [continue for all missing skills]

OVERALL MATCH SCORE: [X out of 10]

HONEST ASSESSMENT:
[Two sentences on how ready the candidate is and what to do first]

Job Requirements Analysis:
{jd_analysis}

Candidate's Current Skills:
{candidate_skills}
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are ARIA, an AI career assistant. Be honest and specific. Always respond in the exact format requested."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content


def generate_resume_bullets(raw_experience, jd_analysis):
    prompt = f"""
You are ARIA, an expert AI career assistant and professional resume writer.
Rewrite the candidate's raw experience as powerful resume bullet points
that match the job description language and pass ATS screening.

Rules:
- Start every bullet with a strong action verb
- Include numbers and metrics wherever possible
- Use keywords from the job description naturally
- Show impact not just tasks
- Write 5 to 7 bullet points total

Respond in EXACTLY this format — no extra text:

REWRITTEN RESUME BULLETS:
- [bullet 1]
- [bullet 2]
- [bullet 3]
- [bullet 4]
- [bullet 5]
- [add more if needed]

KEYWORDS USED FROM JD:
[comma separated list of JD keywords included]

ATS SCORE ESTIMATE: [X out of 10]

IMPROVEMENT TIPS:
- [specific tip 1]
- [specific tip 2]

Job Description Analysis:
{jd_analysis}

Candidate's Raw Experience:
{raw_experience}
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are ARIA, an expert resume writer. Always use strong action verbs. Always respond in the exact format requested."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content


def main():
    print("=" * 55)
    print("         ARIA — JOB DESCRIPTION ANALYSER")
    print("=" * 55)

    file_path = input("Enter the JD filename (e.g. sample_jd.txt): ").strip()
    jd_text = read_jd_from_file(file_path)

    if jd_text is None:
        return

    print()
    print("Analysing job description...")
    print()

    jd_result = analyse_job_description(jd_text)

    print(jd_result)
    print()
    print("=" * 55)

    print()
    print("Now let's check your skill match.")
    print("Enter your current skills separated by commas.")
    print("Example: Python, FastAPI, Docker, SQL, REST APIs")
    print()
    candidate_skills = input("Your skills: ").strip()

    print()
    print("Analysing skill gap...")
    print()

    gap_result = analyse_skill_gap(jd_result, candidate_skills)

    print("=" * 55)
    print("         ARIA — SKILL GAP ANALYSIS")
    print("=" * 55)
    print(gap_result)
    print()
    print("=" * 55)
    print("Analysis complete.")
    print("=" * 55)

    print()
    print("Want to generate resume bullets for this role?")
    generate = input("Enter y for yes, anything else to skip: ").strip().lower()

    if generate == "y":
        print()
        print("Describe your relevant experience in plain words.")
        print("Example: I built a REST API using Flask for an e-commerce app.")
        print()
        raw_experience = input("Your experience: ").strip()

        print()
        print("Generating resume bullets...")
        print()

        bullets = generate_resume_bullets(raw_experience, jd_result)

        print("=" * 55)
        print("     ARIA — RESUME BULLET GENERATOR")
        print("=" * 55)
        print(bullets)
        print()
        print("=" * 55)
        print("Done. Copy these bullets into your resume.")
        print("=" * 55)


if __name__ == "__main__":
    main()