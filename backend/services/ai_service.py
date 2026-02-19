import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class AIService:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.1-8b-instant"
    
    async def analyze_resume(self, resume_text: str, jd_text: str):
        system_prompt = """
You are a world-class, universal recruitment expert with deep expertise across ALL industries, departments, and job functions (Tech, Marketing, Sales, Finance, Healthcare, Engineering, etc.).
Your goal is to evaluate the provided RESUME against the JOB DESCRIPTION (JD) with extreme precision.

CORE RESPONSIBILITY:
1.  **Analyze the Job Description** to identify the **EXACTLY 4** most critical COMPETENCY DATA (dimensions) required for success in this specific role.
    *   *Examples:*
        *   For a Developer: "Frameworks", "Cloud Tools", "Architecture", "Debugging".
        *   For a Marketer: "Content Strategy", "SEO/SEM", "Analytics", "Campaign Mgmt".
        *   For a Sales Rep: "Lead Gen", "Closing", "CRM Proficiency", "Negotiation".
2.  **Score the Candidate** on specific dimensions based on the Resume.

SCORING RULES (The "Radar" Approach):
*   Center Point (10.0) = The Job Description (Perfect Match).
*   Inner Circle (7.0 - 9.0) = High Match / Expert Level relative to JD.
*   Middle Circle (4.0 - 6.0) = Medium Match / Competent.
*   Outer Circle (1.0 - 3.0) = Low Match / Beginner or Missing.

RESPONSE FORMAT:
You MUST return ONLY a valid JSON object with the following structure:
{
    "similarity_score": float (0-100 overall match),
    "upload_summary": "1-2 sentence summary of what the candidate is vs what the JD wants",
    "scores": {
        "Dimension 1 Name": float,
        "Dimension 2 Name": float,
        "Dimension 3 Name": float,
        "Dimension 4 Name": float
    },
    "dimension_definitions": {
        "Dimension 1 Name": "Brief explanation...",
        "Dimension 2 Name": "Brief explanation...",
        "Dimension 3 Name": "Brief explanation...",
        "Dimension 4 Name": "Brief explanation..."
    },
    "analysis": {
        "circle": "Inner" | "Middle" | "Outer",
        "strengths": ["string"],
        "weaknesses": ["string"],
        "reasons": {
            "strengths": "detailed explanation",
            "weaknesses": "detailed explanation"
        }
    },
    "interview_questions": {
        "easy": ["string"],
        "medium": ["string"],
        "hard": ["string"]
    } 
}
Generate exactly 3 easy, 3 medium, and 3 hard interview questions.
CRITICAL INSTRUCTION FOR INTERVIEW QUESTIONS:
1. **Identify Weaknesses First**: Look at the "weaknesses" list you generated.
2. **Easy Questions**: Validates the candidate's existing strengths.
3. **Medium & Hard Questions**: MUST BE DIRECTLY about the specific tools/skills listed in "weaknesses".
   - IF weakness is "Docker", ask about Dockerfiles, layers, or orchestration.
   - IF weakness is "SQL", ask about joins, indexing, or normalization.
   - **DO NOT** generate generic "How do you stay updated" or "Describe a project" questions for Medium/Hard. They MUST test the missing technical skills.

STRENGTHS FALLBACK RULE:
If the candidate has NO strengths or NO matching with the job description, do NOT leave the strengths list empty. Instead:
1. Add this exact string to the "strengths" list: "The candidate has no strengths and no matching with the job description"
2. Set "reasons.strengths" to: "The candidate's profile does not align with the requirements of this role."
3. Set "similarity_score" to a very low value (e.g., 0-5%).
"""

        user_content = f"""
RESUME:
{resume_text}

JOB DESCRIPTION:
{jd_text}
"""

        response = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            model=self.model,
            response_format={"type": "json_object"},
            temperature=0.1
        )

        return json.loads(response.choices[0].message.content)
