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

import json
import re

gravity = {
    "storage-abiencoderv2-array": "High",
    "arbitrary-from-in-transferfrom": "High",
    "modifying-storage-array-by-value": "High",
    "abi-encodePacked-collision": "High",
    "incorrect-shift-in-assembly": "High",
    "multiple-constructor-schemes": "High",
    "name-reused": "High",
    "protected-variables": "High",
    "public-mappings-with-nested-variables": "High",
    "right-to-left-override-character": "High",
    "state-variable-shadowing": "High",
    "suicidal": "High",
    "uninitialized-state-variables": "High",
    "uninitialized-storage-variables": "High",
    "unprotected-upgradeable-contract": "High",
    "codex": "High",
    "arbitrary-from-in-transferfrom-used-with-permit": "High",
    "functions-that-send-ether-to-arbitrary-destinations": "High",
    "array-length-assignment": "High",
    "controlled-delegatecall": "High",
    "payable-functions-using-delegatecall-inside-a-loop": "High",
    "incorrect-exponentiation": "High",
    "incorrect-return-in-assembly": "High",
    "msgvalue-inside-a-loop": "High",
    "reentrancy-vulnerabilities": "High",
    "return-instead-of-leave-in-assembly": "High",
    "storage-signed-integer-array": "High",
    "unchecked-transfer": "High",
    "weak-PRNG": "High",
    "domain-separator-collision": "Medium",
    "dangerous-enum-conversion": "Medium",
    "incorrect-erc20-interface": "Medium",
    "incorrect-erc721-interface": "Medium",
    "dangerous-strict-equalities": "Medium",
    "contracts-that-lock-ether": "Medium",
    "deletion-on-mapping-containing-a-structure": "Medium",
    "state-variable-shadowing-from-abstract-contracts": "Medium",
    "tautological-compare": "Medium",
    "tautology-or-contradiction": "Medium",
    "write-after-write": "Medium",
    "misuse-of-a-boolean-constant": "Medium",
    "constant-functions-using-assembly-code": "Medium",
    "constant-functions-changing-the-state": "Medium",
    "divide-before-multiply": "Medium",
    "out-of-order-retryable-transactions": "Medium",
    "reentrancy-vulnerabilities-1": "Medium",
    "reused-base-constructors": "Medium",
    "dangerous-usage-of-txorigin": "Medium",
    "unchecked-low-level-calls": "Medium",
    "unchecked-send": "Medium",
    "uninitialized-local-variables": "Medium",
    "unused-return": "Medium",
    "incorrect-modifier": "Low",
    "builtin-symbol-shadowing": "Low",
    "local-variable-shadowing": "Low",
    "uninitialized-function-pointers-in-constructors": "Low",
    "pre-declaration-usage-of-local-variables": "Low",
    "void-constructor": "Low",
    "calls-inside-a-loop": "Low",
    "missing-events-access-control": "Low",
    "missing-events-arithmetic": "Low",
    "dangerous-unary-expressions": "Low",
    "missing-zero-address-validation": "Low",
    "reentrancy-vulnerabilities-2": "Low",
    "reentrancy-vulnerabilities-3": "Low",
    "return-bomb": "Low",
    "block-timestamp": "Low",
    "assembly-usage": "Informational",
    "assert-state-change": "Informational",
    "boolean-equality": "Informational",
    "cyclomatic-complexity": "Informational",
    "deprecated-standards": "Informational",
    "unindexed-erc20-event-parameters": "Informational",
    "function-initializing-state": "Informational",
    "incorrect-using-for-usage": "Informational",
    "low-level-calls": "Informational",
    "missing-inheritance": "Informational",
    "conformance-to-solidity-naming-conventions": "Informational",
    "different-pragma-directives-are-used": "Informational",
    "redundant-statements": "Informational",
    "incorrect-versions-of-solidity": "Informational",
    "unimplemented-functions": "Informational",
    "unused-imports": "Informational",
    "unused-state-variable": "Informational",
    "costly-operations-inside-a-loop": "Informational",
    "dead-code": "Informational",
    "reentrancy-vulnerabilities-4": "Informational",
    "too-many-digits": "Informational",
    "cache-array-length": "Optimization",
    "state-variables-that-could-be-declared-constant": "Optimization",
    "public-function-that-could-be-declared-external": "Optimization",
    "state-variables-that-could-be-declared-immutable": "Optimization",
    "public-variable-read-in-external-context": "Optimization",
}

def verify_elements(dictionary, vulnerabilities):
    for vulnerability in vulnerabilities:
        if vulnerability not in dictionary or dictionary[vulnerability] not in ["Optimization", "Informational"]:
            return False
    return True

def revise():
    with open('output/data.json') as f:
        data = json.load(f)

    stats = {}

    for m in data:
        stats[m] = {}
        stats[m]['compilation'] = {}
        stats[m]['zeroVulnerability'] = 0
        stats[m]['vulnerability'] = {}
        stats[m]['vulnerability']['Low'] = 0
        stats[m]['vulnerability']['Medium'] = 0
        stats[m]['vulnerability']['High'] = 0
        stats[m]['vulnerability']['Informational'] = 0
        stats[m]['vulnerability']['Optimization'] = 0
        stats[m]['perfectTests'] = 0
        stats[m]['totalRatio'] = 0
        stats[m]['PerfectContract'] = 0
        stats[m]['details'] = {}
        
        compiledTotal = 0
        notCompiledTotal = 0

        for p in data[m]:
            compiled = 0
            notCompiled = 0

            stats[m]['details'][p] = {}
            stats[m]['details'][p]["compilation"] = {}
            stats[m]['details'][p]["zeroVulnerability"] = 0
            stats[m]['details'][p]['vulnerability'] = {}
            stats[m]['details'][p]['vulnerability']['Low'] = 0
            stats[m]['details'][p]['vulnerability']['Medium'] = 0
            stats[m]['details'][p]['vulnerability']['High'] = 0
            stats[m]['details'][p]['vulnerability']['Informational'] = 0
            stats[m]['details'][p]['vulnerability']['Optimization'] = 0
            stats[m]['details'][p]['perfectTests']= 0
            stats[m]['details'][p]['totalRatio'] = 0
            stats[m]['details'][p]['PerfectContract'] = 0
            
            for it in data[m][p]:
                if (data[m][p][it]["compilation"]['returnCode'] == 0):
                    compiledTotal += 1
                    compiled += 1
                    
                    temp = []
                    for d in gravity:
                        if (data[m][p][it]["slither"]['stderr'].lower().count(("https://github.com/crytic/slither/wiki/Detector-Documentation#" + d).lower())):
                            temp.append(d)

                        stats[m]['vulnerability'][gravity[d]] = stats[m]['vulnerability'][gravity[d]] + data[m][p][it]["slither"]['stderr'].lower().count(("https://github.com/crytic/slither/wiki/Detector-Documentation#" + d).lower())
                        stats[m]['details'][p]['vulnerability'][gravity[d]] = stats[m]['details'][p]['vulnerability'][gravity[d]] + data[m][p][it]["slither"]['stderr'].lower().count(("https://github.com/crytic/slither/wiki/Detector-Documentation#" + d).lower())
                    
                    if (verify_elements(gravity, temp)):
                        stats[m]['zeroVulnerability'] += 1
                        stats[m]['details'][p]["zeroVulnerability"] += 1
                    
                    if (data[m][p][it]["testing"]['returnCode'] == 0):
                        stats[m]['perfectTests'] += 1
                        stats[m]['details'][p]['perfectTests'] += 1
                    
                    texte = data[m][p][it]["testing"]['stdout']
                    passing_match = re.search(r'(\d+) passing', texte)
                    failing_match = re.search(r'(\d+) failing', texte)

                    passing = int(passing_match.group(1)) if passing_match else 0
                    failing = int(failing_match.group(1)) if failing_match else 0

                    total_tests = passing + failing

                    if total_tests > 0:
                        ratio = passing / total_tests
                    else:
                        ratio = 0
                    
                    if (ratio == 1 and data[m][p][it]["testing"]['returnCode'] == 0 and verify_elements(gravity, temp)):
                        stats[m]['PerfectContract'] += 1 
                        stats[m]['details'][p]['PerfectContract'] += 1 
                    
                    stats[m]['totalRatio'] += (ratio*100)
                    stats[m]['details'][p]['totalRatio'] += (ratio*100)
                
                else :
                    notCompiledTotal += 1
                    notCompiled += 1
                    
            stats[m]['details'][p]["compilation"]['ok'] = compiled
            stats[m]['details'][p]["compilation"]['ko'] = notCompiled

            if (compile == 0):
                stats[m]['details'][p]["compilation"]['ratio'] = 0
            else:
                stats[m]['details'][p]["compilation"]['ratio'] = compiled/(compiled + notCompiled)*100
            
            if (compiled != 0):
                stats[m]['details'][p]['totalRatio'] /= compiled
                
        stats[m]['compilation']['ok'] = compiledTotal
        stats[m]['compilation']['ko'] = notCompiledTotal
        stats[m]['compilation']['ratio'] = stats[m]['compilation']['ok']/(compiledTotal + notCompiledTotal)*100
        
        if (compiledTotal != 0):
            stats[m]['totalRatio'] /= compiledTotal
                
    with open("output/stats.json", "w") as fichier:
        json.dump(stats, fichier, indent = 4)

if __name__ == '__main__':
    revise()