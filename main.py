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

from pipeline import compute
from analyze import revise

import subprocess

if __name__ == '__main__':
    compute()
    revise()
    
    print("\nCompression of the result in: ./pipeline_output.zip")
    
    subprocess.run(['zip', '-r', "output_pipeline", "output"], capture_output=True, text=True)