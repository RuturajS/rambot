import os
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class AIAnalyzer:
    def __init__(self):
        self.reload_config()

    def reload_config(self):
        self.provider = os.getenv("AI_PROVIDER", "openai").lower()
        self.model = os.getenv("AI_MODEL", "gpt-4o-mini")
        
        # API Keys
        self.openai_key = os.getenv("OPENAI_API_KEY") or os.getenv("AI_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")

        self.client = None
        self._init_client()

    def _init_client(self):
        if self.provider == "openai" and self.openai_key:
            self.client = OpenAI(api_key=self.openai_key)
        
        elif self.provider == "anthropic" and self.anthropic_key:
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=self.anthropic_key)
            except ImportError:
                print("Anthropic SDK not installed.")
        
        elif self.provider == "gemini" and self.gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                self.client = genai.GenerativeModel(self.model)
            except ImportError:
                 print("Google GenerativeAI SDK not installed.")

        elif self.provider == "openrouter" and self.openrouter_key:
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.openrouter_key,
            )

    def _get_response(self, messages):
        """Unified response handler."""
        if not self.client:
            return f"Error: Client for {self.provider} not initialized. Check API Key."

        try:
            # OpenAI / OpenRouter
            if self.provider in ["openai", "openrouter"]:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages
                )
                return response.choices[0].message.content

            # Anthropic
            elif self.provider == "anthropic":
                # Convert messages to string prop or use generic format
                # Anthropic SDK has specific format
                system = next((m['content'] for m in messages if m['role'] == 'system'), "")
                user_msgs = [m for m in messages if m['role'] != 'system']
                
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    system=system,
                    messages=user_msgs
                )
                return response.content[0].text

            # Gemini
            elif self.provider == "gemini":
                # Setup prompt
                prompt = messages[-1]['content']
                response = self.client.generate_content(prompt)
                return response.text

        except Exception as e:
            return f"API Error ({self.provider}): {str(e)}"

    def analyze(self, file_path, query):
        try:
            df = pd.read_excel(file_path)
            excel_data = df.to_csv(index=False)
            # Limit data size for reliability
            if len(excel_data) > 100000:
                excel_data = excel_data[:100000] + "\n...(truncated)"

            prompt = f"""
You have access to an Excel file with this data:
{excel_data}

User question: {query}

Provide a concise answer with calculations if needed.
"""
            messages=[
                {"role": "system", "content": "You are a helpful data analyst assistant."},
                {"role": "user", "content": prompt}
            ]
            return self._get_response(messages)
            
        except Exception as e:
            return f"Error during analysis: {str(e)}"

    def edit(self, file_path, instruction, output_path):
        try:
            df = pd.read_excel(file_path)
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
            messages=[{"role": "user", "content": prompt}]
            content = self._get_response(messages)
            
            # Simple error check on content
            if content.startswith("Error:") or content.startswith("API Error"):
                return False, content

            import re
            code_match = re.search(r"```python(.*?)```", content, re.DOTALL)
            if code_match:
                code_str = code_match.group(1).strip()
            else:
                code_str = content.replace("```python", "").replace("```", "").strip()

            print(f"Executing Code ({self.provider}):\n{code_str}")

            local_vars = {"df": df, "pd": pd}
            exec(code_str, {}, local_vars)
            
            df_new = local_vars["df"]
            df_new.to_excel(output_path, index=False)
            
            return True, "File edited successfully."
            
        except Exception as e:
            return False, f"Error editing file: {str(e)}"

