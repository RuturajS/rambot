import os
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class AIAnalyzer:
    def __init__(self):
        self.api_key = os.getenv("AI_API_KEY")
        self.model = os.getenv("AI_MODEL", "gpt-4o-mini")
        self.client = None
        if self.api_key:
             self.client = OpenAI(api_key=self.api_key)

    def analyze(self, file_path, query):
        if not self.client:
            return "Error: AI_API_KEY not found in environment variables."

        try:
            # Load Excel Data
            # Reading with pandas. 
            # Ideally we check file extension, but assuming valid excel from logic
            df = pd.read_excel(file_path)
            
            # Convert to string for prompt
            # Using to_csv for a compact representation
            excel_data = df.to_csv(index=False)
            
            # Truncate if too long? 
            # For MVP, let's assume it fits or simple error if too large.
            # Basic character limit check could be good but skipping for "ultra minimal" unless it fails.
            
            prompt = f"""
You have access to an Excel file with this data:
{excel_data}

User question: {query}

Provide a concise answer with calculations if needed.
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful data analyst assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Error during analysis: {str(e)}"

    def edit(self, file_path, instruction, output_path):
        if not self.client:
             return False, "Error: AI_API_KEY not found."
        
        try:
            df = pd.read_excel(file_path)
            # Provide columns and types to LLM for context
            columns_info = df.dtypes.to_string()
            sample_data = df.head(3).to_string()

            prompt = f"""
You are a Python data manipulation expert.
I have a pandas DataFrame named `df` loaded from an Excel file.
Structure:
{columns_info}

Sample Data:
{sample_data}

User Instruction: {instruction}

Write a Python code snippet to modify `df` in-place according to the instruction.
- Do NOT read or write files.
- ONLY `df` modification code.
- Wrap code in ```python ... ```
"""
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.choices[0].message.content
            # Extract code block
            import re
            code_match = re.search(r"```python(.*?)```", content, re.DOTALL)
            if code_match:
                code_str = code_match.group(1).strip()
            else:
                code_str = content.replace("```python", "").replace("```", "").strip()

            print(f"Executing Code:\n{code_str}") # Debug log

            # Execute
            local_vars = {"df": df, "pd": pd}
            exec(code_str, {}, local_vars)
            
            # Retrieve modified df
            df_new = local_vars["df"]
            df_new.to_excel(output_path, index=False)
            
            return True, "File edited successfully."
            
        except Exception as e:
            return False, f"Error editing file: {str(e)}"

