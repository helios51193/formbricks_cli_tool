from pprint import pprint
import cuid2
from openai import OpenAI
import requests
import json
import os
from dotenv import load_dotenv
from tqdm import tqdm
import uuid
from pprint import pprint
from datetime import datetime, timezone

from pathlib import Path

load_dotenv('cli.env')

class DataInjester():

    def __init__(self):
        self.formbricks_host = os.getenv("FORMBRICKS_HOST","http://localhost:3000")
        self.environment_key = os.getenv("ENVIRONMENT_ID",None)
        self.API_KEY = os.getenv("API_KEY",None)

        self.formbricks_paths = Path("formbricks")
        self.formbricks_paths.mkdir(exist_ok=True)

    def _id(self):
        return uuid.uuid4().hex[:24]
   
    
    # Convert the generated survey into formbricks payload
    def _survey_questions_to_blocks(self,generated_survey):
        OPERATOR_MAP = {
            "<=": "isLessThanOrEqual",
            "<": "isLessThan",
            ">": "isGreaterThan",
            ">=": "isGreaterThanOrEqual",
            "==": "equals",
            "!=": "notEquals",
        }

        questions = generated_survey["survey"]["questions"]

        # Map question_id -> block cuid
        qid_to_block = {
            q["question_id"]: self._id()
            for q in questions
        }

        blocks = []

        for q in questions:
            qid = q["question_id"]
            qtype = q["question_type"]

            # ---------- Question ----------
            fb_question = {
                "id": qid,
                "type": qtype,
                "required": q["logic"].get("required", False),
                "headline": {"default": q["question_text"]}
            }

            if qtype == "rating":
                fb_question.update({
                    "range": q["config"]["rating"]["max_value"],
                    "scale": "star",
                    "isColorCodingEnabled": False,
                    "lowerLabel": {"default": "Not satisfied"},
                    "upperLabel": {"default": "Very satisfied"},
                })

            if qtype == "openText":
                fb_question.update({
                    "inputType": "text",
                    "placeholder": {
                        "default": q["config"]["text"].get("placholder", "")
                    }
                })

            # ---------- Logic ----------
            logic_conditions = q["logic"].get("conditions", [])
            fb_logic = []
            if logic_conditions:
                for rule in logic_conditions:
                    rule_if = rule["if"]
                    operator = OPERATOR_MAP[rule_if["operator"]]

                    fb_logic.append({
                        "id":self._id(),
                        "conditions": {
                            "id":self._id(),
                            "connector": "and",
                            "conditions": [
                                {
                                    "id":self._id(),
                                    "operator": operator,
                                    "leftOperand": {
                                        "type": "element",
                                        "value": qid
                                    },
                                    "rightOperand": {
                                        "type": "static",
                                        "value": rule_if["value"]
                                    }
                                }
                            ]
                        },
                        "actions": [
                            {
                                "id":self._id(),
                                "objective": "jumpToBlock",
                                "target": qid_to_block[rule_if["go_to"]]
                            }
                        ]
                    })
            # ---------- Block ----------
            block = {
                "id": qid_to_block[qid],
                "name": f"Block for {qid}",
                "type": "question",
                "elements": [fb_question]
            }
            if len(fb_logic) > 0:
                block["logic"] = fb_logic 

            blocks.append(block)


        payload = {
            "name": generated_survey["survey"]["name"],
            "type": "link",
            "status": "inProgress",
            "environmentId": self.environment_key,
            "blocks": blocks,
            "questions": [],
            "endings": [],
            "hiddenFields": {"enabled": False, "fieldIds": []}
}
        return payload

    
    # Convert the generated answer into formbricks payload
    def _build_formbricks_response_payload(self, survey_id, answers, language="en",finished=True):
        now = datetime.now(timezone.utc).isoformat()

        data = {}

        for ans in answers['answers']:
            qid = ans["question_id"]
            value = ans["value"]

            # Formbricks expects arrays as values
            data[qid] = value

        return {
            "createdAt": now,
            "updatedAt": now,
            "finished": finished,
            "language": language,
            "surveyId": survey_id,
            "environmentId": self.environment_key,
            "data": data
        }


    # Save the ids returned from uploading surveys 
    def _save_formbricks_ids(self, ids):

        with open(self.formbricks_paths/ "formbricks_ids.json","w") as f:
            json.dump(ids, f)
    
    
    # Generate formbricks surveys from LLM generated surveys and upload 
    def _generate_formbricks_survey_json_and_upload(self):
        
        directory = Path("surveys")

        formbricks_jsons = {}
        
        for json_file in directory.rglob("*.json"):
            print(f"Processing: {json_file}")

            survey = {}
            with json_file.open("r", encoding="utf-8") as f:
                survey = json.load(f)

                payload = self._survey_questions_to_blocks(survey)
                formbricks_jsons[str(json_file)] = payload
        
        
        survey_ids = self._upload_surveys(formbricks_jsons)

        self._save_formbricks_ids(survey_ids)


    # Generate formbricks answers from LLM generated answers and upload 
    def _generate_formbricks_survey_answer_json_upload(self):
        
        survey_id_path = Path("formbricks")
        answers_directory = Path("answers")

        formbricks_ids = {}

        with open(survey_id_path / "formbricks_ids.json") as f:
            formbricks_ids = json.load(f)

        
        survey_ids = {}
        for question, id in formbricks_ids.items():
            
            file_name = question.split("/")
            survey_id = file_name[1].split(".")[0].split("_")[1]
            print(survey_id)
            survey_ids[survey_id] = id

        
        print(survey_ids)
        for id,fb_id in survey_ids.items():

            answers_path = answers_directory / f"answers_{id}.json"

            
            if not answers_path.exists():
                print(f"Answers for {id} does not exists")
                continue
            
            answers = {}

            with open(answers_path) as f:
                answers = json.load(f)

            answers_formatted = {}

            for user_id, answer in answers.items():
                temp = self._build_formbricks_response_payload(survey_id=fb_id, answers=answer)
                answers_formatted[user_id] = temp
            
            # with open(f"answers_{fb_id}.json","w") as f:
            #     json.dump(answers_formatted,f, indent=2)
            
            self._upload_answers(answers_formatted)

    
    # Upload surveys using API
    def _upload_surveys(self, jsons):
        
        survey_ids = {}
        
        header = self._get_header()
        url = f"{self.formbricks_host}/api/v1/management/surveys"
        
        for id,survey in jsons.items():
            res = requests.post(url=url, headers=header, data=json.dumps(survey))
            if res.status_code == 200:
                data = res.json()
                survey_ids[id] = data['data']['id']
            else:
                survey_ids[id] = "ERROR"
        
        return survey_ids

    # Upload answers using API
    def _upload_answers(self, jsons):

        header = self._get_header()
        url = f"{self.formbricks_host}/api/v1/management/responses"

        for answer in tqdm(jsons.values(), desc="Uploading Answers for survey"):
            res = requests.post(url=url, headers=header, data=json.dumps(answer))
            

    
    # Get api key
    def _get_header(self):

        return {
            "x-api-key":self.API_KEY
        }

    # Check if previous steps have been taken or not
    def can_proceed(self):

        try:
            # check for api keys
            if not self.environment_key or not self.API_KEY:
                return False,"No enviroment key or api key"
            
            # check if file exists and are valid
            survey_directory = Path("surveys")
            answer_directory = Path("answers")
            survey_ids = []
            answer_ids = []
            for json_file in survey_directory.rglob("*.json"):
                stem = json_file.stem
                survey_id = stem.split("_")[1]
                survey_ids.append(survey_id)
            
            for json_file in answer_directory.rglob("*.json"):
                stem = json_file.stem
                answer_id = stem.split("_")[1]
                answer_ids.append(answer_id)
            
            if len(survey_ids) != len(answer_ids):
                return False, "surveys and answers count are not matching, equal amount of file not there"

            intr = set(survey_ids) & set(answer_ids)
            if intr != set(survey_ids):
                return False, "surveys and answers ids are not matching"


        
            return True, "all good"
        except Exception as e:
            return False, f"Some Error :{e}, cannot proceed"

    # Main function to handle seeding
    def seed(self):

        status, msg = self.can_proceed()
        if not status:
            print(msg)
            return

        
        #self._generate_formbricks_survey_json_and_upload()
        self._generate_formbricks_survey_answer_json_upload()



if __name__ == "__main__":

    test = DataInjester()
    test.seed()
    #test.test()