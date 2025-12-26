from pprint import pprint
from openai import OpenAI
import requests
import json
import os
from dotenv import load_dotenv
from tqdm import tqdm

from pathlib import Path

load_dotenv('cli.env')

class DataGenerator():

    def __init__(self):

        self._key = os.getenv("OPEN_AI_KEY", None)


        self.survey_prompt = """
                        You are generating a survey definition.

                        Rules:
                        - Output MUST be valid JSON
                        - Do NOT add explanations
                        - Do NOT invent platform-specific fields
                        - Use short stable question IDs: q1, q2, q3
                        - Include conditional logic if appropriate
                        - Define the type of question

                        Survey goal:
                        << survey_goal >>

                        Question types allowed:
                        - rating (1-5 stars)
                        - openText
                        - single choice
                        - multiple choice



                        JSON schema:
                        << schema >>
                                
                        """

        self.answer_prompt = """
                                You are generating synthetic survey responses.

                                STRICT RULES:
                                - Output MUST be valid JSON
                                - Output MUST match the provided answer schema exactly
                                - Do NOT include explanations, comments, or markdown
                                - Do NOT add fields not defined in the schema
                                - All responses must respect survey logic and visibility rules
                                - Check the logic and only provide the answers of the relevant questions
                                - Only answer questions that would be shown to the user

                                INPUT 1 — Survey Definition (JSON):
                                << survey_json >>

                                INPUT 2 — Answer Schema (JSON):
                                << answer_schema_json >>

                                TASK:
                                Generate realistic responses for << N >> different users.

                                CONSTRAINTS:
                                - Rating values must be within the allowed range
                                - Text answers must be realistic and varied
                                - If a question is conditionally visible, include it ONLY when its condition is met
                                - Do NOT generate answers for hidden questions
                                - Use stable user IDs: user_001, user_002, ...

                                OUTPUT:
                                Return ONLY a JSON object that conforms to the answer schema.                    

                            """

    def _load_survey_prompts(self):

        self.survey_prompts = {}

        with open("prompts/survey_description_prompts.json") as f:
            self.survey_prompts = json.load(f)
        

    def _generate_survey_prompt(self, survey_prompt):

        self._load_survey_prompts()

        question_schema = None
        with open("schemas/question_schema.json") as f:
            question_schema = json.load(f)
        prompt = self.survey_prompt.replace("<< schema >>", json.dumps(question_schema))
        prompt = prompt.replace("<< survey_goal >>", survey_prompt)
        return prompt
    

    def _generate_answer_prompt(self, survey_json, n):

        answer_schema = {}
        with open("schemas/answer_schema.json") as f:
            answer_schema = json.load(f)
        
        prompt = self.answer_prompt.replace("<< answer_schema_json >>", json.dumps(answer_schema)) \
                                    .replace("<< survey_json >>", json.dumps(survey_json)) \
                                    .replace("<< N >>", str(n))
    
        return prompt
        

    def _save_survey(self, question, id):
        
        ques_path = Path("surveys")

        ques_path.mkdir(exist_ok=True)

        with open(f"surveys/survey_{id}.json","w") as f:
            json.dump(obj=question, fp=f, indent=2)
    
    def _save_answers(self, answers, id):

        answer_path = Path("answers")

        answer_path.mkdir(exist_ok=True)

        with open(f"answers/answers_{id}.json","w") as f:
            json.dump(obj=answers, fp=f, indent=2)
    

    def generate_survey(self):

        

        if not self._key:
            print("No OPEN AI Key provided")
            return
        
        self._load_survey_prompts()

        client = OpenAI(api_key=self._key)


        for survey_prompt in tqdm(self.survey_prompts['surveys'], desc="Generating Surveys"):
            prompt = self._generate_survey_prompt(survey_prompt['prompt'])

            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                        "role": "system",
                        "content": "You output ONLY valid JSON. No explanations."
                }, 
                {
                    "role": "user",
                    "content":prompt
                }],
                response_format={ "type": "json_object" }
            )

            data = json.loads(resp.choices[0].message.content)
            self._save_survey(data, survey_prompt['id'])


    def _get_survey(self, id):

        file_path = f"surveys/survey_{id}.json"
        if not os.path.exists(file_path):
            print(f"{file_path} does not exist")
            return None

        with open(file_path) as f:
            return json.load(f)    
    
    def generate_answers(self, n = 5):
        
        print(f"Generating {n} answers for each question")
        self._load_survey_prompts()
        
        if not self._key:
            print("No OPEN AI Key provided")
            return

        client = OpenAI(api_key=self._key)
        for survey_prompt in tqdm(self.survey_prompts['surveys'], desc=f"Generating Surveys answers, {n} each"):
            survey = self._get_survey(survey_prompt["id"])
            if not survey:
                print(f"No survey generated for {survey_prompt['id']}")
                continue
            
            prompt = self._generate_answer_prompt(survey,n)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                        "role": "system",
                        "content": "You output ONLY valid JSON. No explanations."
                }, 
                {
                    "role": "user",
                    "content":prompt
                }],
                response_format={ "type": "json_object" }
            )

            data = json.loads(resp.choices[0].message.content)
            self._save_answers(data, survey_prompt['id'])              

    def generate(self, n=5):

        self.generate_survey()
        self.generate_answers(n=n)

if __name__ == "__main__":

    aa = DataGenerator()
    aa.generate()
    






    
