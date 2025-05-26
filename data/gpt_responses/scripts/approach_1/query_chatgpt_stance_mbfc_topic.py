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
    with open(f"output-{model_name}-stance-topic.jsonl", "r") as f:
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

def get_completion(site, topic, model=model_name):
    system_prompt = f"You are an assistant to help the user determine the stance of a website on certain topic."
    prompt = f"What is the stance of {{0}} on {{1}}. \nAssistant should return the stance and the reason in JSON format, and do not provide anything else.".format(site,topic)
    
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
    

### 

def get_stance(site, topic, model=model_name):
    sleep_time = 1
    try:
        i = 0
        while True and i < 5:
            try:
                response = get_completion(site, topic, model=model)
                response = json.loads(response)
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


topics = ['Ukraine', 'Climate Change', 'Gun Control', 'Immigration', 'Abortion']

with open(f"output-{model_name}-stance-topic.jsonl", "a") as f:
    with tqdm(total=len(websites)) as pbar:
        for site in websites:
            output = {}
            output[site] = {}
            for topic in topics:
                text_output = get_stance(site, topic)
                if text_output:
                    output[site][topic] = text_output    
                    time.sleep(1)
                else:
                    output[site][topic] = {
                        "error": "404"
                    }

            json.dump(output, f)
            f.write('\n')

            pbar.update(1)