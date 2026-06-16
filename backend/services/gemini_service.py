import os

from dotenv import load_dotenv

from google import genai
from google.genai import types

load_dotenv()

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# =====================================================
# GENERIC GENERATION
# =====================================================

def generate_text(
    prompt,
    model="gemini-2.5-flash"
):

    try:

        response = client.models.generate_content(

            model=model,

            contents=prompt,

            config=types.GenerateContentConfig(
                temperature=0.3,
                top_p=0.9,
                max_output_tokens=4000
            )
        )

        return response.text

    except Exception as e:

        return f"Gemini Error: {str(e)}"


# =====================================================
# RNA-SEQ REPORT
# =====================================================

def generate_rnaseq_report(
    prompt
):

    return generate_text(
        prompt=prompt,
        model="gemini-2.5-flash"
    )


# =====================================================
# SHORT INSIGHTS
# =====================================================

def generate_dataset_insights(
    prompt
):

    return generate_text(
        prompt=prompt,
        model="gemini-2.5-flash"
    )


# =====================================================
# DRUG REPURPOSING INSIGHTS
# =====================================================

def generate_drug_repurposing_insights(
    prompt
):

    return generate_text(
        prompt=prompt,
        model="gemini-2.5-flash"
    )