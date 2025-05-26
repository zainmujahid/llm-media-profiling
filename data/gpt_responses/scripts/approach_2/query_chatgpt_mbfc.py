import json
import openai
import time
from tqdm import tqdm
import argparse
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument("--input_file", help="Path to the input data file", required=True) # MBFC file with websites
args = parser.parse_args()

input_file_path = args.input_file

df = pd.read_csv(input_file_path)
websites = df["domain"].tolist()

print(f"Total Number of websites to process: {len(set(websites))}")


###############################################################
defs = {
    'General Philosophy':{
        'left':'Collectivism: Community over the individual. Equality, environmental protection, expanded educational opportunities, social safety nets for those who need them.',
        'right':'Individualism: Individual over the community. Limited Government with Individual freedom and personal property rights. Competition.',
    },
    'Abortion':{
        'left': 'Legal in most cases.',
        'right': 'Generally illegal with some exceptions.',
    },
    'Economic Policy':{
        'left': 'Income equality; higher tax rates on the wealthy; government spending on social programs and infrastructure; stronger regulations on business. Minimum wages and some redistribution of wealth.',
        'right': 'Lower taxes; less regulation on businesses; reduced government spending.  The government should tax less and spend less. Charity over social safety nets. Wages should be set by the free market.',
    },
    'Education Policy':{
        'left': 'Favor expanded free, public education. Reduced cost or free college.',
        'right': 'Supports homeschooling and private schools. Generally not opposed to public education, but critical of what is taught.',
    },
    'Environmental Policy':{
        'left': 'Regulations to protect the environment. Climate change is human-influenced and immediate action is needed to slow it.',
        'right': 'Considers the economic impact of environmental regulation. Believe the free market will find its own solution to environmental problems, including climate change. Some deny climate change is human-influenced.',
    },
    'Gay Rights':{
        'left': 'Generally support gay marriage; support anti-discrimination laws to protect LGBT against workplace discrimination.',
        'right': 'Generally opposed to gay marriage; opposed to certain anti-discrimination laws because they believe such laws conflict with certain religious beliefs and restrict freedom of religion.',
    },
    'Gun Rights':{
        'left': 'Favors laws such as background checks or waiting periods before buying a gun; banning certain high capacity weapons to prevent mass shootings.',
        'right': 'Strong supporters of the Second Amendment (the right to bear arms), believing it’s a deterrent against authoritarian rule and the right to protect oneself. Generally, does not support banning any type of weaponry.',
    },
    'Health Care':{
        'left': 'Most support universal healthcare; strong support of government involvement in healthcare, including Medicare and Medicaid. Generally, support the Affordable Care Act. Many believe healthcare is a human right.',
        'right': 'Believe private companies can provide healthcare services more efficiently than government-run programs. Oppose the Affordable Care Act. Insurance companies can choose what to cover and compete with each other. Healthcare is not a right.',
    },
    'Immigration':{
        'left': 'Generally, support a moratorium on deporting or offering a pathway to citizenship to certain undocumented immigrants. e.g. those with no criminal record, who has lived in the U.S. for 5+ years. Less restrictive legal immigration.',
        'right': 'Generally against amnesty for any undocumented immigrants. Oppose a moratorium on deporting certain workers. Funding for stronger enforcement actions at the border (security, wall). More restrictive legal immigration.',
    },
    'Military':{
        'left': 'Decreased Spending',
        'right': 'Increased Spending',
    },
    'Personal Responsibility':{
        'left': 'Strong government to provide a structure. Laws are enacted to protect every individual for an equal society. Safety nets for those in need.',
        'right': 'Personal responsibility and it is the government’s role to hold them accountable. Fair competition over safety nets.',
    },
    'Regulation':{
        'left': 'Government regulations are needed to protect consumers and the environment.',
        'right': 'Government regulations hinder free-market capitalism and job growth.',
    },
    'Social Views':{
        'left': 'Based on community and social responsibility. Gay couples to get equal rights like everyone else (e.g. marriage); abortion should be legal; support embryonic stem cell research. Support restrictions and regulations around the right to bear arms. Supports taxpayer funding of Planned Parenthood.',
        'right': 'Based on individual rights and justice. Opposed to gay marriage, abortion, and embryonic stem cell research. Support the right to bear arms, death penalty, and personal responsibility as an individual. Opposed to taxpayer funding of Planned Parenthood.',
    },
    'Taxes':{
        'left': 'Progressive taxation (high-income earners taxed at a higher rate). Generally not opposed to raising taxes to fund the government.',
        'right': 'Tend to favor a “flat tax” (same tax rate regardless of income). Generally opposed to raising taxes to fund the government.',
    },
    'Voter ID':{
        'left': 'Against voter ID laws citing an undue burden on lower-income groups causing them to be disenfranchised, and that there is virtually no evidence of voter fraud actually occurring.',
        'right': 'For voter identification laws to combat alleged voter fraud.',
    },
    "Business Rights":{
        'left': 'Supports unions and worker protections. Raising the minimum wage. Higher corporate taxes.',
        'right': 'Favors business owners and corporations with the expectation higher profits will result in higher wages through a free-market. Generally opposed to a minimum wage. Lower corporate taxes.',
    },

}
###############################################################


###############################################################

openai.api_key = "API-KEY-HERE"  # Replace with your OpenAI API key
openai.organization = "YOUR-ORG-ID-HERE"  # Replace with your OpenAI organization ID if applicable
model_name = "gpt-3.5-turbo-1106"

############ To remove the sites already processed ############
#                       As Per New Data
###############################################################

try:
    old_sites = []
    with open(f"gpt_responses/bias_methodology/output-{model_name}-mbfc-method-bias-3-labels.jsonl", "r") as f:
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

def get_completion(site, topic, left, right, model=model_name):
    system_prompt = f'''
    You are an expert journalist to help user determine the bias leaning of a media on topic, "{{0}}". Return "leaning" and the "reason" in JSON format. Consider your training data as the evidence. Return "unknown" if you can not determine the leaning. 

    Labels Definition: 
    - left: {{1}}
    - right: {{2}}'''.format(topic, left, right)
    prompt = f"{{0}}".format(site)
    
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

def get_bias_leaning(site, topic, left, right, model=model_name):
    sleep_time = 0.02
    try:
        i = 0
        while True and i < 5:
            try:
                response = get_completion(site, topic, left, right, model=model)
                response = json.loads(response)
                if 'leaning' in response and 'reason' in response:
                    time.sleep(sleep_time)
                    break
            except Exception as e:
                print(f"Error: {e}. Retrying ({i+1}/5)...")
                time.sleep(sleep_time)
                sleep_time *= 5
                i += 1
                continue
        return response
    except Exception as e:
        print(f"Error: {e}. Returning empty string...")
        return ""


with open(f"./gpt_responses/bias_methodology/output-{model_name}-mbfc-method-bias-3-labels.jsonl", "a") as f:
    with tqdm(total=len(websites)) as pbar:
        for site in websites:
            output = {}
            output[site] = {}
            for topic in list(defs.keys()):
                output[site][topic] = {}
                left = defs[topic]['left']
                right = defs[topic]['right']
                text_output = get_bias_leaning(site, topic, left, right)
                if text_output:
                    output[site][topic] = text_output
                else:
                    output[site][topic] = {
                        "error": "404"
                    }

            # Write the output dictionary to the JSON file
            json.dump(output, f)
            f.write('\n')

            pbar.update(1)