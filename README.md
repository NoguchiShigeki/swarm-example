# Swarm Complete Monolithic

## Overview

Swarm Complete Monolithic is a Python, OpenAI Swarm, and OpenAI grade-school-math benchmark datasets based multi-agent system designed to execute benchmark tests or handle custom user prompts using OpenAI's language models.
It leverages multiple agents to collaboratively debate and arrive at consensus answers, making it suitable for tasks such as evaluating mathematical problem-solving capabilities or generating comprehensive responses to user queries.

## Features

- **Multi-Agent Collaboration:** Deploy multiple agents to collaboratively solve problems through debate rounds.
- **Benchmark Testing:** Run standardized benchmarks (e.g., 1k math problems) to evaluate the system's performance.
- **User Prompt Mode:** Input custom prompts and receive aggregated responses from the agent swarm.
- **Comparative Experiment:** Compare multi-agent performance against a single zero-shot agent.
- **Detailed Logging:** Save conversation histories, inputs, and benchmark results for analysis.
- **Error Handling:** Robust handling of API key validation, rate limits, and connectivity issues.

## Prerequisites

- **Python 3.7 or higher**
- **OpenAI API Key:** Required to access OpenAI's language models.

## Installation

1. **Clone the Repository:**

   ```shell
   git clone https://github.com/NoguchiShigeki/swarm-example.git
   cd swarm-example
   ```

2. **Set Up a Virtual Environment:**

   It's recommended to use a virtual environment to manage dependencies.

   ```shell
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate
   ```

3. **Install Dependencies:**

   Install the required Python packages using `pip`.

   ```shell
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**

   Refactor a `.env` file in the project root directory and add your OpenAI API key.

   ```dotenv
   OPENAI_API_KEY=sk-your-openai-api-key
   ```

   **Note:** If the `.env` file is not found or the `OPENAI_API_KEY` is not set, the program will prompt you to input the API key manually during execution.

## Usage

Execute the `swarm_complete_monolithic.py` script using Python.

```shell
python3 swarm_complete_monolithic.py
```

### Execution Steps

1. **Select Mode:**

   Upon running the script, you will be prompted to select an execution mode.

   ```shell
   Select a mode: 
   [1] Run a 1k math benchmark (grade-school-math by OpenAI)
   [2] User prompt mode
   Select the mode: <1 or 2>
   ```

   - **Mode 1:** Runs a predefined set of 1,000 math benchmark questions to evaluate the system's performance.
   - **Mode 2:** Allows you to input custom prompts and receive aggregated responses from the agent swarm.

2. **Configure Agents and Debate Rounds:**

   You will be asked to specify:
   
   - **Number of Agents:** Determines how many agents will participate in the debate.
   - **Number of Debate Rounds:** Specifies how many rounds of debate the agents will engage in to refine their answers.

   ```shell
   Enter the number of agents (Agent's model is 'gpt-4o-mini-2024-07-18'): <number>
   Enter the number of debate rounds: <number>
   ```

3. **Benchmark Mode Specifics (Mode 1):**

   - **Benchmark Length:**

     Specify the number of benchmark questions to run.

     ```shell
     Enter the number of benchmark questions you want to run: <number>
     ```

   - **Comparative Experiment:**

     Optionally, run a comparative experiment against a single zero-shot agent.

     ```shell
     Do you want to run a comparative experiment? (Run and Compare with a Single Agent Zero-shot) (y/n): <y or n>
     ```

4. **User Prompt Mode Specifics (Mode 2):**

   - **Input User Prompt:**

     Enter a custom prompt. If left blank, a sample question will be used.

     ```shell
     Enter an user prompt (Blank input will use a sample question):
     ```

     **Sample Input:**

     ```shell
     Tom has a red marble, a green marble, a blue marble, and three identical yellow marbles. How many different groups of two marbles can Tom choose?
     ```

5. **Execution and Output:**

   - **Benchmark Mode:**

     The system will process each question through multiple agents and debate rounds, aggregate the final answers, and compare them against the correct answers. Results, including accuracy and elapsed time, will be displayed and saved to output files.

     **Sample Output:**

     ```shell
     #### Multi-Agent Benchmark Summary ####
     Total Questions: 1000
     Elapsed time: 3600.00 seconds
     Correct Answers: 950
     Accuracy: 95.00%

     ==== Benchmark Summary Zero Shot Single ====
     Total Questions: 1000
     Elapsed time: 1800.00 seconds
     Correct Answers: 900
     Accuracy: 90.00%
     ```

   - **User Prompt Mode:**

     The system will process the input prompt through multiple agents and debate rounds, then aggregate the final conclusion.

     **Sample Output:**

     ```shell
     The conclusion from the final agent:
     Tom can choose from 7 different groups of two marbles.

     Grading result: True
     ```

6. **Output Files:**

   All results and conversation histories are saved in a timestamped `output_<timestamp>` directory within the project folder. The following files are generated:

   - **`conversation_history_<timestamp>.json`**: Detailed logs of all conversations between agents and the user.
   - **`all_inputs_<timestamp>.json`**: Records of all inputs provided to the agents during execution.
   - **`benchmark_result_<timestamp>.json`**: Results of the benchmark tests, including correctness and conclusions.
   - **`summary_<timestamp>.json`**: A summary of benchmark results and, if applicable, comparative experiment results.

## Example Workflow

1. **Run Benchmark Mode:**

   ```shell
   python3 swarm_complete_monolithic.py
   ```

   **Interaction:**

   ```shell
   Select a mode: 
   [1] Run a 1k math benchmark (grade-school-math by OpenAI)
   [2] User prompt mode
   Select the mode: 1

   Enter the number of agents (Agent's model is 'gpt-4o-mini-2024-07-18'): 5
   Enter the number of debate rounds: 3
   Enter the number of benchmark questions you want to run: 1000
   Do you want to run a comparative experiment? (Run and Compare with a Single Agent Zero-shot) (y/n): y
   ```

   **Output:**

   ```shell
   #### Multi-Agent Benchmark Summary ####
   Total Questions: 1000
   Elapsed time: 3600.00 seconds
   Correct Answers: 950
   Accuracy: 95.00%

   ==== Benchmark Summary Zero Shot Single ====
   Total Questions: 1000
   Elapsed time: 1800.00 seconds
   Correct Answers: 900
   Accuracy: 90.00%
   ```

2. **Run User Prompt Mode:**

   ```shell
   python3 swarm_complete_monolithic.py
   ```

   **Interaction:**

   ```shell
   Select a mode: 
   [1] Run a 1k math benchmark (grade-school-math by OpenAI)
   [2] User prompt mode
   Select the mode: 2

   Enter the number of agents (Agent's model is 'gpt-4o-mini-2024-07-18'): 3
   Enter the number of debate rounds: 2
   Enter an user prompt (Blank input will use a sample question):
   ```

   **Output:**

   ```shell
   The conclusion from the final agent:
   Tom can choose from 7 different groups of two marbles.

   Grading result: True
   ```

## Notes

- **API Key Security:** Ensure your OpenAI API key is kept secure. Do not expose it in public repositories or logs.
- **Rate Limits:** Be mindful of OpenAI's API rate limits to avoid interruptions. The script includes handling for rate limit errors.
- **Customizing Agents:** You can modify agent instructions or models by editing the `swarm_complete_monolithic.py` script as needed.
- **Extensibility:** The system is designed to be extensible. You can integrate more complex tasks or different benchmarks by adjusting the input data and agent instructions.

## Troubleshooting

- **Missing `.env` File:**

  If the `.env` file is not found or the `OPENAI_API_KEY` is not set, the script will prompt you to input the API key manually.

  ```shell
  .env File Not Found.
  OpenAI API Key is required to run.
  ...
  Enter OpenAI API Key Here: sk-xxxx
  ```

- **Invalid API Key:**

  Ensure that the provided API key is correct. An invalid key will result in authentication errors.

  ```shell
  Provided OpenAI API Key is Invalid❌
  Enter OpenAI API Key Here: sk-xxxx
  ```

- **Rate Limit Exceeded:**

  If you encounter rate limit errors, consider reducing the number of concurrent agents or upgrading your OpenAI plan.

  ```shell
  Provided API Key has reached the rate limit.
  ```

- **File Not Found:**

  Ensure that the `test.jsonl` file exists in the current directory for benchmark mode.

  ```shell
  File not found: There is no such a file "test.jsonl" in the current directory where this script exists
  ```

## Contributing

Contributions are welcome! Please open issues or submit pull requests for enhancements, bug fixes, or new features.

## Acknowledgements

- **OpenAI:** For providing the language models and API infrastructure.
- **Swarm Framework:** For the multi-agent system architecture.

---

*Happy Hacking!*
