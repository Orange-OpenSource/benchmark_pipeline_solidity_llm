# Software Name : benchmark_pipeline_solidity_llm
# SPDX-FileCopyrightText: Copyright (c) Orange SA
# PDX-License-Identifier: GPL-3.0-only
# 
# This software is distributed under the GNU GENERAL PUBLIC LICENSE
# see the "LICENSE.txt" file for more details or https://spdx.org/licenses/GPL-3.0-only.html
# 
# Authors: DURAND Mathis - <mathis.durand@orange.com>
#          DASPE Etienne - <etienne.daspe@orange.com>
# Software description: This pipeline generates solidity smart contracts using LLM models.
# It compiles and analyses them, performs unit tests and produces statistics on the models
# ability to produce efficient code.

import os
import pandas as pd
import re
import requests
import json
import subprocess

from yaspin import yaspin

subprocess.run(["solc-select", "install", "0.8.25"], capture_output=True, text=True)
subprocess.run(["solc-select", "use", "0.8.25"], capture_output=True, text=True)

nbIteration = 1
models = ["llama3",
          "gemma",
          "mistral",
          "codegemma",
          "codellama"]

def cleanRepo():    
    if os.path.exists("output"):
        os.system('rm -rf {}'.format("output"))
    
    os.mkdir("output")
    os.mkdir("output/extracted_tests")

def initDataset(dataSetName):
    df = pd.read_csv(dataSetName, sep=";", encoding='latin1')
    
    nbPrompts = df.shape[0]
    
    print("input : " + dataSetName + " (" + str(nbPrompts) + " prompts)")
    
    dataset = [None] * nbPrompts

    print("\t- [NAME]: [CHARS LONG] [TESTS ?]")
    
    for i in range(nbPrompts):
        dataset[i] = [df.iat[i, 0], df.iat[i, 1], df.iat[i, 1]]
        pattern = r"```js(.*?)```"
        res = re.findall(pattern, df.iat[i, 1], re.DOTALL)

        if res:
            content = res[0]
            with open("output/extracted_tests/" + df.iat[i, 0] + ".js", 'w') as fichier:
                fichier.write(content)

        print("\t- " + dataset[i][0] + ":  " + str(len(dataset[i][1])) + " "*3 + str(os.path.exists("output/extracted_tests/" + dataset[i][0] + ".js")))
        
    print("\n")

    return dataset

def initModels():
    global models
    
    print("models: " + str(models))
    
    return models

def fetchOllama(model, prompt, temperature=0.2):
    url = "http://localhost:11434/api/generate"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature
        }
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

def compute():
    global nbIteration
    
    cleanRepo()
        
    dataset = initDataset("simple_dataset.csv")
    
    models = initModels()
    
    print("Iteration per model&prompt = " + str(nbIteration) + "\n")
    
    results = {}
    
    if (os.path.exists("hardhat_test_env/contracts") == False):
        os.mkdir("hardhat_test_env/contracts")
    if (os.path.exists("hardhat_test_env/test") == False):
        os.mkdir("hardhat_test_env/test")
    
    for i in range(len(models)):
        m = models[i]

        if (os.path.exists("output/" + m) == False):
            os.mkdir("output/" + m)
        
        totalDurationModel = 0
        contratsPos = 0
        promptPos = 1

        print("• " + m + " is working!")

        with yaspin(text="Processing...") as spinner:
            results[m] = {}
            
            for j in range(len(dataset)):
                prompt = dataset[j]

                if (os.path.exists("output/" + m + "/" + prompt[0]) == False):
                    os.mkdir("output/" + m + "/" + prompt[0])
                    
                results[m][prompt[0]] = {}
                    
                for k in range(nbIteration):
                    spinner.text = "Processing... "
                    
                    #STEP 1 : generates the output

                    results[m][prompt[0]][k] = {}
                    results[m][prompt[0]][k]["compilation"] = {}
                    results[m][prompt[0]][k]["slither"] = {}
                    results[m][prompt[0]][k]["testing"] = {}
                    
                    try:
                        res = fetchOllama(m, prompt[1])

                        res.pop("context")
                        res.pop("model")

                        results[m][prompt[0]][k]["response"] = res["response"]
                        
                        with open("output/" + m + "/" + prompt[0] + "/" + str(k) + ".txt", 'w') as fichier:
                            fichier.write(res["response"])
                        
                        res.pop("response")

                        results[m][prompt[0]][k]["promptInfos"] = res
                        
                        totalDurationModel += res['total_duration']
                        
                        #STEP 1 bis : cleaning the response
                        
                        with open("output/" + m + "/" + prompt[0] + "/" + str(k) + ".txt", 'r') as file:
                            content = file.read()

                        pattern = re.compile(r'```(.*?)```', re.DOTALL)
                        matches = pattern.findall(content)

                        with open("output/" + m + "/" + prompt[0] + "/" + str(k) + ".sol", 'w') as output_file:
                            for match in matches:
                                match = match.strip()
                                lines = match.split('\n')

                                if lines[0] == "solidity":
                                    lines = lines[1:]
                                    
                                match = '\n'.join(lines)
                                first_line = lines[0]
                
                                # If the LLM "forgets" to generate the SPDX-License-Identifier line, we write it to avoid compilation warnings
                                if not first_line.startswith('// SPDX-License-Identifier:'):
                                    output_file.write('// SPDX-License-Identifier: UNLICENSED\n')
                                    
                                output_file.write(match + '\n')
                        
                        #STEP 2 : Compilation

                        result = subprocess.run(["solc", "--gas", "--bin" , "output/" + m + "/" + prompt[0] + "/" + str(k) + ".sol"], capture_output=True, text=True)                        
                        results[m][prompt[0]][k]["compilation"]['returnCode'] = result.returncode
                        results[m][prompt[0]][k]["compilation"]['stdout'] = result.stdout
                        results[m][prompt[0]][k]["compilation"]['stderr'] = result.stderr
                        
                        #STEP 3 : Slither

                        result = subprocess.run(["slither", "output/" + m + "/" + prompt[0] + "/" + str(k) + ".sol"], capture_output=True, text=True)
                        results[m][prompt[0]][k]["slither"]['returnCode'] = result.returncode
                        results[m][prompt[0]][k]["slither"]['stdout'] = result.stdout
                        results[m][prompt[0]][k]["slither"]['stderr'] = result.stderr
                        
                        #STEP 4 : Hardhat & testing

                        subprocess.run(["rm", "hardhat_test_env/contracts/contract.sol"], capture_output=True, text=True)
                        subprocess.run(["cp", "output/" + m + "/" + prompt[0] + "/" + str(k) + ".sol","hardhat_test_env/contracts/contract.sol"], capture_output=True, text=True)
                    
                        subprocess.run(["rm", "hardhat_test_env/test/verify.js"], capture_output=True, text=True)
                        subprocess.run(["cp", "output/extracted_tests/" + prompt[0] + ".js","hardhat_test_env/test/verify.js"], capture_output=True, text=True)
                        
                        result = subprocess.run(["npx", "hardhat", "test"], cwd = "hardhat_test_env", capture_output=True, text=True)
                        results[m][prompt[0]][k]["testing"]['returnCode'] = result.returncode
                        results[m][prompt[0]][k]["testing"]['stdout'] = result.stdout
                        results[m][prompt[0]][k]["testing"]['stderr'] = result.stderr
                        
                        
                        print("Process finished! contract: [" + str(promptPos) + "/" + str(len(dataset)) + "], iteration: [" + str(k + 1) + "/" + str(nbIteration) + "]")
                    except:
                        results[m][prompt[0]][k]["response"] = "error"

                        print("Error! contract: [" + str(promptPos) + "/" + str(len(dataset)) + "], iteration: [" + str(k + 1) + "/" + str(nbIteration) + "]")
            
                    contratsPos += 1

                promptPos += 1
            
            spinner.text = ""
            spinner.ok("✔ Done! " + str(contratsPos) + " outputs\n")

            print("Info :\n\ttotalDurationModel= " + str(totalDurationModel/1e9) + " s")

    with open("output/data.json", "w") as file:
        json.dump(results, file, indent=4)

if __name__ == '__main__':
    print("-"*70 + "\n" + " "*23 + " LLM bench : pipeline.py" + " "*23 + "\n" + "-"*70)
    compute()
    print("-"*70)
