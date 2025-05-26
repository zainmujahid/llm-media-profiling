import json
import openai
import time
from tqdm import tqdm
import argparse
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument("--input_file", help="Path to the input data file", required=True)
args = parser.parse_args()

input_file_path = args.input_file

df = pd.read_csv(input_file_path)
websites = df["domain"].tolist()
print(f"Total Number of websites to process: {len(set(websites))}")

###############################################################

openai.api_key = "API-KEY-HERE"  # Replace with your OpenAI API key
openai.organization = "YOUR-ORG-ID-HERE"  # Replace with your OpenAI organization ID if applicable
model_name = "gpt-3.5-turbo-1106"

############ To remove the sites already processed ############
try:
    old_sites = []
    with open(f"output-{model_name}-trust.jsonl", "r") as f:
        for line in f:
            json_obj = json.loads(line)
            old_sites.append(list(json_obj.keys())[0])

    websites = list(set(websites) - set(old_sites))
    print(f"Unifinished file found.")
    print(f"Total Number of remaining websites to process: {len(websites)}")
except:
    print("No unfinished file found")
    pass
###############################################################

def get_completion(prompt, model=model_name):
    system_prompt = f"You are an assistant to help the user determine the credibility of a website."
    messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}]
    
    response = openai.ChatCompletion.create(
                    model=model,
                    messages=messages,
                    temperature=0,
                    max_tokens=256,
                    top_p=0.5,
                    frequency_penalty=0,
                    presence_penalty=0,
                    request_timeout=30,
                    response_format= {
                        'type': 'json_object',
                    }
                )
    return response.choices[0].message["content"]
    

### TODO: re-write this fucntion

def get_trust(prompt, model=model_name):
    sleep_time = 1
    try:
        i = 0
        while True and i < 5:
            try:
                response = get_completion(prompt, model=model)
                response = json.loads(response)
                ### check if response object doesnt have the required keys stance and reason, then throw exception
                if 'answer' not in response.keys() or 'reason' not in response.keys():
                    raise Exception("Response object doesnt have the required keys answer and reason")
                break                
            except Exception as e:
                print(f"Error: {e}. Retrying ({i+1}/5)...")
                time.sleep(sleep_time)
                sleep_time *= 2
                i += 1
                continue
        return response
    except Exception as e:
        print(f"Error: {e}. Returning empty string...")
        return ""


def get_prompts(site):
    prompts = []
    default_text = "\nAssistant must return the 'answer' and 'reason' in JSON format, and do not provide anything else."
    ques_1 = f"Can I trust {{0}}. Answer in 1 word.{{1}}".format(site, default_text)
    ques_2 = f"Has {{0}} failed fact-checks? Answer in one word.{{1}}".format(site, default_text)
    ques_3 = f"IS {{0}} LEFT, CENTER, or Right. Answer in one word.{{1}}".format(site, default_text)
    ques_4 = f"IS {{0}} Biased.{{1}}".format(site, default_text)
    ques_5 = f"Characterize {{0}} in 3 words.{{1}}".format(site, default_text)
    ques_6 = f"Characterize the bias of {{0}} in 3 words.{{1}}".format(site, default_text)  
    prompts = [ques_1, ques_2, ques_3, ques_4, ques_5, ques_6]  
    return prompts



with open(f"output-{model_name}-trust.jsonl", "a") as f:
    with tqdm(total=len(websites)) as pbar:
        for site in websites:
            output = {}
            output[site] = {}
            prompts = get_prompts(site)
            count = 0 
            for prompt in prompts:
                text_output = get_trust(prompt)
                if text_output:
                    output[site][count] = text_output    
                else:
                    output[site][count] = {
                        "error": "404"
                    }
                count += 1

            # Write the output dictionary to the JSON file
            json.dump(output, f)
            f.write('\n')

            pbar.update(1)