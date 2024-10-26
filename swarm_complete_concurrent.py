# Disclaimer: My comments are tedious but it is for the readability and understanding of the code.
# It is included my chains of thoughts and the reason why I put the comments in the code.
# TODO: Threading or asyncio to speed up the process; wait till each agent finishes each round.
import openai
from swarm import Swarm, Agent
from dotenv import load_dotenv
import os
import time
import json
import sys
import re
import datetime
from pathlib import Path
import concurrent.futures  # Added for threading
import threading  # Added for thread-safe operations

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print(".env File Not Found.")
    print("OpenAI API Key is required to run.")
    print("You must let the API Key to use models from OpenAI Settings > Project > Limit")
    while True:
        try:
            api_key = input("Enter OpenAI API Key Here: ")
            if not api_key:
                raise ValueError("OpenAI API Key is not typed.")
            break
        except Exception as e:
            print(f"Input Error: {e}\nType OpenAI API Key again.")
else:
    print("OpenAI API Key is Found!")
    print("Remember, let the API Key to use models from OpenAI Settings > Project > Limit")

openai.api_key = api_key

# Validate API Key
try:
    oai_response = openai.models.list()
    if oai_response:
        print("Provided OpenAI API Key is Valid✅")
except openai.AuthenticationError:
    print("Provided OpenAI API Key is Invalid❌")
    while True:
        try:
            api_key = input("Enter OpenAI API Key Here: ")
            if not api_key:
                raise ValueError("OpenAI API Key is not typed.")
            break
        except Exception as e:
            print(f"Input Error: {e}\nType OpenAI API Key again.")
except openai.RateLimitError:
    print("Provided API Key has reached the rate limit.")
    sys.exit(1)
except openai.APIConnectionError:
    print("Failed to connect to the OpenAI API.\nCheck your internet connection🛜")
    sys.exit(1)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    sys.exit(1)

client = Swarm()

# Reading GSM benchmark from this directory
try:
    with open("test.jsonl", "r", encoding="utf-8") as f:
        data = [json.loads(line) for line in f]
except FileNotFoundError:
    print("File not found: There is no such a file \"test.jsonl\" in the current directory where this script exists")
    sys.exit(1)

# Making a directory to store the output files
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
output_directory = Path(f"output_{timestamp}")
try:
    output_directory.mkdir(parents=True, exist_ok=True)
except Exception as e:
    print(f"An error occurred while creating the output directory: {e}")
    sys.exit(1)

# Declare the question and answer list
questions = [item["question"] for item in data]
answers = [item["answer"] for item in data]

# Ask the user to select a mode
while True:
    try:
        mode = int(input(
            "Select a mode: \n[1] Run a 1k math benchmark (grade-school-math by OpenAI)\n[2] User prompt mode\nSelect the mode: "))
        if mode not in [1, 2]:
            raise ValueError("Mode must be [1] or [2]")
        break
    except ValueError as e:
        print(f"Input Error: {e} \nSelect a mode again")

# Ask the user to input the number of agents and debate rounds
while True:
    try:
        agent_number = int(input("Enter the number of agents (Agent's model is 'gpt-4o-mini-2024-07-18'): "))
        if agent_number <= 0:
            raise ValueError("The number of agents must be more than 0")
        break
    except ValueError as e:
        print(f"Input Error: {e} \nEnter the number of agent again")

while True:
    try:
        debate_round_number = int(input("Enter the number of debate rounds: "))
        if debate_round_number <= 0:
            raise ValueError("The number of debate rounds must be more than 0")
        break
    except ValueError as e:
        print(f"Input Error: {e} \nEnter the number of debate rounds again")

if mode == 1:
    while True:
        try:
            benchmark_length = int(input("Enter the number of benchmark questions you want to run: "))
            if benchmark_length <= 0:
                raise ValueError("The number of benchmark questions must be more than 0")
            break
        except ValueError as e:
            print(f"Input Error: {e} \nEnter the number of benchmark questions again")
    # Overwrite and slice Answers and Questions from benchmark datasets
    questions = questions[:benchmark_length]
    answers = answers[:benchmark_length]

# Ask the user if they want to run a comparative experiment
if mode == 1:
    while True:
        try:
            comparative_experiment = input(
                "Do you want to run a comparative experiment? (Run and Compare with a Single Agent Zero-shot) (y/n): ")
            if comparative_experiment in ["Y", "y"]:
                ce_flag = True
            elif comparative_experiment in ["N", "n"]:
                ce_flag = False
            if comparative_experiment not in ["y", "n", "Y", "N"]:
                raise ValueError("You have to use either Y/N or y/n.")
            break
        except ValueError as e:
            print(f"Input Error: {e} \nType in your intention again.")

# Ask the user to input a user prompt if the mode is 2, otherwise use a sample input
if mode == 2:
    user_prompt = input("Enter an user prompt (Blank input will use a sample question): ")

# Start of the time
start = time.time()

# Create a list to store agent instances
# They named same, but they are different agents, the iterator knows it's different. it is like human and person, they are same but different.
agents = []

# Create agents based on input (This is common for both modes)
# gpt-4o-mini-2024-07-18 is used
for i in range(agent_number):
    agent = Agent(
        name=f"Agent {i + 1}",
        # If you want to add a persona to the agents, you can change the instructions here, e.g., "Pretend that you are a very creative person."
        instructions=f"You are agent {i + 1}. You are one of the agents in a multi-agent system.",
        # You can specify a model by adding attribute like this model="gpt-3.5-turbo",
        model="gpt-4o-mini-2024-07-18",
    )
    agents.append(agent)

# The aggregator: This is used to aggregate the responses of agents in the final round. (For mode 1)
# gpt-4o-mini-2024-07-18 is used
aggregator = Agent(
    name="Aggregator",
    instructions=(
        "You are part of a Collaborative Debate Model, a multi-agent system where agents independently propose solutions and critique each other's responses over multiple rounds. "
        "Your role is to aggregate the final responses from all agents in the final round. "
        "You do only aggregate the responses in the final round but not to alter or review and update responses. "
        "Aggregate the responses from agents to find the majority opinion, and make a final consensus answer. "
        "Output must be follow this format: **<A consensus answer>**. "
    ),
    model="gpt-4o-mini-2024-07-18",
)

# The grader: This is required for the grading of the multi-agent system (For mode 1)
# Grader must be smart, therefore I used GPT-4o (Default of the Swarm Framework)
grader = Agent(
    name="Grader",
    instructions=(
        "You are part of a Collaborative Debate Model, a multi-agent system where agents propose solutions and refine their answers through multiple rounds of debate. "
        "Compare the consensus answer in a format of **<A consensus answer>** with the answer label and determine whether it is correct ('True') or incorrect ('False')."
        "Respond to the user with 'True' or 'False'"
    ),
)

# These instructions are used in the messages for the agents during execution
instruction_initial = "Make sure to state your answer at the end of the response."
instruction_debate_1 = "These are the recent/updated opinions from other agents:"
instruction_debate_2 = "Use these opinions carefully as additional advice, and provide an updated answer. Make sure to state your answer at the end of the response."

# Initialize a lock for thread-safe operations
lock = threading.Lock()

# Conditional Branch depends on the mode:
# If mode is 1, run a benchmark, if mode is 2, get an user prompt
if mode == 1:
    # Re-define the aggregator and the grader
    # The aggregator: This is used to aggregate the responses of agents in the final round.
    # gpt-4o-mini-2024-07-18 is used
    aggregator = Agent(
        name="Aggregator",
        instructions=(
            "You are part of a Collaborative Debate Model, a multi-agent system where agents independently propose solutions and critique each other's responses over multiple rounds. "
            "Your role is to aggregate the final responses from all agents in the final round. "
            "You do only aggregate the responses in the final round but not to alter or review and update responses. "
            "Aggregate the responses from agents to find the majority opinion, and make a final <Consensus Answer>. "
            "Other than Consensus Answer, there must be a numeric answer agents are supposed to solve simple grade math problems, there is a sole numeric <Answer> in your aggregated answer. "
            "You can write a process in Consensus Answer, but you must not in <Answer>. "
            "The answer must not include any form of alphabets or symbol only digits, if your answer includes a some kind of symbols, you must write a numeric answer in <Answer>."
            "Your output must be like this: <Consensus Answer> #### <Answer>"
        ),
        model="gpt-4o-mini-2024-07-18",
    )

    # The grader: This is required for the grading with labels of the multi-agent system
    # Grader must be smart, therefore I used GPT-4o (Default of the Swarm Framework)
    # He is fired now, because I introduced rule based grading below, however, it should be needed when the task and benchmark would be more complex than this, for now R.I.P.

    # Loop through the questions and grade and store the result in to list
    benchmark_result = []
    # benchmark_result.append({"index": k, "question": questions[k], "answer": answers[k], "conclusion": conclusion, "result": grading_result}) at the finale of the question
    # Global conversation history with the initial user message and the initial question index
    conversation_history = []
    # This is required for debugging and checking the input side history
    all_inputs = []
    for k in range(len(questions)):
        print(f"No. {k + 1} Question initiated")
        # Fetch a question and answer for the corresponding current index
        question = questions[k]
        answer = answers[k]
        match = re.search(r"####\s*(\d+)", answer)
        numeric_answer = float(match.group(1)) if '.' in match.group(1) else int(match.group(1))
        question_index = k + 1

        # Overwrite a user_input
        user_input = [
            {
                "role": "user",
                "content": f"{question} {instruction_initial}",
            }
        ]
        label = f"{numeric_answer}"

        conversation_history.append(
            {
                "name": "User",
                "role": "user",
                "content": user_input[0]["content"],
                "round": 0,
                "question_index": question_index,
            }
        )

        # Loop through the debates and come to a conclusion over the specified number of debate rounds
        for j in range(debate_round_number):
            print(f"Debate round {j + 1} initiated")
            if j == 0:
                # Parallelize the first round of agent responses
                def agent_initial_response(agent, agent_id):
                    print(f"Debate {j + 1}: {agent.name} in progress")
                    response = client.run(agent=agent, messages=user_input)
                    with lock:
                        conversation_history.append(
                            {
                                "name": agent.name,
                                "role": "assistant",
                                "content": response.messages[-1]["content"],
                                "round": j + 1,
                                "question_index": question_index,
                            }
                        )
                        all_inputs.append(
                            {
                                "question_index": question_index,
                                "content": user_input,
                                "round": j + 1,
                            }
                        )

                with concurrent.futures.ThreadPoolExecutor(max_workers=agent_number) as executor:
                    executor.map(lambda agent: agent_initial_response(agent, agent.name), agents)

            else:
                # Parallelize the subsequent rounds of agent responses
                def agent_debate_response(agent, agent_id):
                    print(f"Debate {j + 1}: {agent.name} in progress")
                    # Search for the responses from the previous round, excluding the current agent's response
                    last_round_others_responses = [
                        response
                        for response in conversation_history
                        if response["round"] == j and response["question_index"] == question_index and response["name"] != agent.name
                    ]
                    # Find the current agent's last response to allow for self-reflection
                    last_round_own_response = [
                        response
                        for response in conversation_history
                        if response["round"] == j and response["question_index"] == question_index and response["name"] == agent.name
                    ]
                    # Create a self-reflection message if the agent's previous response exists
                    if last_round_own_response:
                        self_reflection_message = f"Your previous response was: {last_round_own_response[0]['content']}. Reflect on your own response and improve it."
                    else:
                        self_reflection_message = ""

                    # Update the messages for the current agent by incorporating the previous round's responses from other agents
                    previous_responses_message = "\n".join(
                        [
                            f"{resp['name']}: {resp['content']}"
                            for resp in last_round_others_responses
                        ]
                    )
                    user_input_with_debate = [
                        {
                            "role": "user",
                            "content": f"{instruction_debate_1} {previous_responses_message}\n\n{self_reflection_message}\n\n{instruction_debate_2}",
                        }
                    ]
                    with lock:
                        all_inputs.append(
                            {
                                "question_index": question_index,
                                "content": user_input_with_debate,
                                "round": j + 1,
                            }
                        )
                    # Pass the previous agents' responses to the current agent
                    response = client.run(
                        agent=agent,
                        messages=user_input_with_debate,  # Updated with other agents' responses
                    )
                    with lock:
                        # Add the latest agent's response to the conversation history
                        conversation_history.append(
                            {
                                "name": agent.name,
                                "role": "assistant",
                                "content": response.messages[-1]["content"],
                                "round": j + 1,
                                "question_index": question_index,
                            }
                        )

                with concurrent.futures.ThreadPoolExecutor(max_workers=agent_number) as executor:
                    executor.map(lambda agent: agent_debate_response(agent, agent.name), agents)

        # Aggregating the final round's responses
        instruction_aggregate = "You are going to conclude the debate by aggregating all agents' responses into a single conclusion. If it is math problem, the last of output must be this format; '#### <The numeric answer>' and this is a math problem, the answer is sole and single."
        final_round_response = [
            response for response in conversation_history if
            response["round"] == debate_round_number and response["question_index"] == question_index
        ]
        final_round_response_message = "\n".join(
            [f"{resp['name']}: {resp['content']}" for resp in final_round_response]
        )
        input_final_round_response = [
            {
                "role": "user",
                "content": f"{instruction_aggregate}\n\n{final_round_response_message}",
            }
        ]
        all_inputs.append(
            {
                "question_index": question_index,
                "content": input_final_round_response,
                "round": "final",
            }
        )

        aggregator_response = client.run(agent=aggregator, messages=input_final_round_response)

        # The final response from the aggregator
        conclusion = aggregator_response.messages[-1]["content"]
        match = re.search(r"####\s*(\d+)", conclusion)
        numeric_conclusion = float(match.group(1)) if '.' in match.group(1) else int(match.group(1))

        # Method Using LLM (which was unstable AF, so I ditched GPT-4o)
        # That method is unstable AF but the more complex the task becomes, the more needs to be used. Thus, remember this method, I have this method in local obsolete/swarm_complete_benchmark.py

        # Grading method using rule-based
        if numeric_answer == numeric_conclusion:
            grading_result = "True"
        else:
            grading_result = "False"

        benchmark_result.append(
            {
                "index": k + 1,
                "question": question,
                "answer": answer,
                "conclusion": conclusion,
                "result": grading_result,
            }
        )

    # Calculate elapsed time
    end = time.time()
    elapsed_time = end - start

    # Generate a timestamp for the filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    ch_filename = Path(output_directory / f"conversation_history_{timestamp}.json")
    ai_filename = Path(output_directory / f"all_inputs_{timestamp}.json")
    result_filename = Path(output_directory / f"benchmark_result_{timestamp}.json")  # Fixed f-string

    # Save all conversations to the file
    try:
        with open(ch_filename, "w", encoding="utf-8") as f:
            json.dump(conversation_history, f, ensure_ascii=False, indent=4)
        print(
            f"Conversation histories have been saved to {ch_filename}\nThere should be chains of thought of the agents.")
    except Exception as e:
        print(f"An error occurred while saving the conversation history: {e}")
    # Save the all inputs to the file
    try:
        with open(ai_filename, "w", encoding="utf-8") as f:
            json.dump(all_inputs, f, ensure_ascii=False, indent=4)
            print(
                f"All inputs have been saved to {ai_filename}\nThe file stores all inputs to the agents")
    except Exception as e:
        print(f"An error occurred while saving the all inputs: {e}")
    # Save the benchmark result to the file
    try:
        with open(result_filename, "w", encoding="utf-8") as f:
            json.dump(benchmark_result, f, ensure_ascii=False, indent=4)
            print(
                f"Benchmark Result has been saved to {result_filename}.\nYou can check the result of the questions in this file.")
    except Exception as e:
        print(f"An error occurred while saving the benchmark result: {e}")

    # Calculation the accuracy
    correct_count = sum(1 for r in benchmark_result if r['result'] == 'True')
    total_questions = len(benchmark_result)
    accuracy = (correct_count / total_questions) * 100 if total_questions > 0 else 0

    print(f"\n#### Multi-Agent Benchmark Summary ####")
    print(f"Total Questions: {total_questions}")
    print("Elapsed time:", elapsed_time)
    print(f"Correct Answers: {correct_count}")
    print(f"Accuracy: {accuracy:.2f}%")

    if ce_flag:
        start_zs = time.time()

        # Do a comparison: gpt-4o-mini-2024-07-18
        agent_zs = Agent(
            name=f"Agent Zero Shot",
            instructions=f"You are a useful agent. You are going to solve a grade math, there must be a sole and numeric <Answer>. The answer does not need to add ','. You must not write a process within the <Answer>. Your response must be #### <Answer> at the last of response.",
            model="gpt-4o-mini-2024-07-18",
        )

        instruction_initial_zs = "Make sure to state your answer at the end of the response in a format of #### <Answer>."

        conversation_zs = []
        results_zs = []

        for i in range(len(questions)):
            question_zs = questions[i]
            answer_zs = answers[i]
            match = re.search(r"####\s*(\d+)", answer_zs)
            numeric_answer_zs = float(match.group(1)) if '.' in match.group(1) else int(match.group(1))
            user_input_zs = [
                {
                    "role": "user",
                    "content": f"{question_zs} {instruction_initial_zs}"
                }
            ]
            label_zs = f"{numeric_answer_zs}"

            # Record the user input to conversation_history for zero-shot
            conversation_zs.append(
                {
                    "name": "User",
                    "role": "user",
                    "content": user_input_zs[0]['content'],
                    "question_index": i + 1,
                }
            )

            response_zs = client.run(agent=agent_zs, messages=user_input_zs)

            conversation_zs.append(
                {
                    "name": agent_zs.name,
                    "role": "assistant",
                    "content": response_zs.messages[-1]["content"],
                    "question_index": i + 1,
                }
            )

            conclusion_zs = response_zs.messages[-1]["content"]
            match = re.search(r"####\s*(\d+)", conclusion_zs)
            numeric_conclusion_zs = float(match.group(1)) if '.' in match.group(1) else int(match.group(1))

            # Rule based
            if numeric_conclusion_zs == numeric_answer_zs:
                grading_result_zs = "True"
            else:
                grading_result_zs = "False"

            results_zs.append(
                {
                    "index": i + 1,
                    "question": question_zs,
                    "answer": answer_zs,
                    "conclusion": conclusion_zs,
                    "result": grading_result_zs,
                }
            )

        end_zs = time.time()
        elapsed_time_zs = end_zs - start_zs

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        ch_filename_zs = Path(output_directory / f"conversation_history_zs_{timestamp}.json")
        result_filename_zs = Path(output_directory / f"benchmark_result_zs_{timestamp}.json")

        try:
            with open(ch_filename_zs, "w", encoding="utf-8") as f:
                json.dump(conversation_zs, f, ensure_ascii=False, indent=4)
            print(f"Conversation histories have been saved to {ch_filename_zs}")
        except Exception as e:
            print(f"An error occurred while saving the conversation history: {e}")

        try:
            with open(result_filename_zs, "w", encoding="utf-8") as f:
                json.dump(results_zs, f, ensure_ascii=False, indent=4)
                print(
                    f"Benchmark results have been saved to {result_filename_zs}.\n If you want to check the conclusion of the questions, check this file.")
        except Exception as e:
            print(f"An error occurred while saving the benchmark result: {e}")

        correct_count_zs = sum(1 for r in results_zs if r['result'] == 'True')
        total_questions_zs = len(results_zs)
        accuracy_zs = (correct_count_zs / total_questions_zs) * 100 if total_questions_zs > 0 else 0

        print(f"\n==== Benchmark Summary Zero Shot Single ====")
        print(f"Total Questions: {total_questions_zs}")
        print("Elapsed time:", elapsed_time_zs)
        print(f"Correct Answers: {correct_count_zs}")
        print(f"Accuracy: {accuracy_zs:.2f}%")

    # Save the benchmark result summary to the file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_filename = Path(output_directory / f"summary_{timestamp}.json")
    try:
        with open(summary_filename, "w", encoding="utf-8") as f:
            if ce_flag:
                f.write(
                    f"==== Benchmark Result {timestamp} with Comparative Experiment (Zero-Shot Single Agent) ====\n")
                f.write("#### Multi-Agent Benchmark Summary ####\n")
                f.write(f"Agents: {agent_number}\n")
                f.write(f"Debate Rounds: {debate_round_number}\n")
                f.write(f"Total Questions: {total_questions}\n")
                f.write(f"Elapsed Time: {elapsed_time:.2f} seconds\n")
                f.write(f"Correct Answers: {correct_count}\n")
                f.write(f"Accuracy: {accuracy:.2f}%\n\n")
                f.write("\n")
                f.write("#### Zero-Shot Single Agent Benchmark Summary ####\n")
                f.write(f"Total Questions: {total_questions_zs}\n")
                f.write(f"Elapsed Time: {elapsed_time_zs:.2f} seconds\n")
                f.write(f"Correct Answers: {correct_count_zs}\n")
                f.write(f"Accuracy: {accuracy_zs:.2f}%\n")
            else:
                f.write(f"==== Benchmark Result {timestamp} ====\n")
                f.write("#### Multi-Agent Benchmark Summary ####\n")
                f.write(f"Agents: {agent_number}\n")
                f.write(f"Debate Rounds: {debate_round_number}\n")
                f.write(f"Total Questions: {total_questions}\n")
                f.write(f"Elapsed Time: {elapsed_time:.2f} seconds\n")
                f.write(f"Correct Answers: {correct_count}\n")
                f.write(f"Accuracy: {accuracy:.2f}%\n")
            print(
                f"Benchmark Summary has been saved to {summary_filename}.\nYou can check the summary of the benchmark.")
    except Exception as e:
        print(f"An error occurred while saving the benchmark result summary: {e}")

elif mode == 2:
    if user_prompt:
        user_input = [
            {
                "role": "user",
                "content": user_prompt,
            }
        ]
    else:
        user_input = [
            {
                "role": "user",
                "content": f"Tom has a red marble, a green marble, a blue marble, and three identical yellow marbles. How many different groups of two marbles can Tom choose? {instruction_initial}",
            }
        ]
        label = "The answer is 7 different groups."
    # Global conversation history with the initial user message
    conversation_history = [
        {"name": "User", "role": "user", "content": user_input[0]["content"], "round": 0}
    ]
    # Loop through the debates and come to a conclusion over the specified number of debate rounds
    for j in range(debate_round_number):
        if j == 0:
            # Parallelize the first round of agent responses
            def agent_initial_response_mode2(agent, agent_id):
                # Pass the entire conversation history to each agent
                response = client.run(agent=agent, messages=user_input)
                with lock:
                    # Add the latest agent's response to the conversation history
                    conversation_history.append(
                        {
                            "name": agent.name,
                            "role": "assistant",
                            "content": response.messages[-1]["content"],
                            "round": j + 1,  # Round 1
                        }
                    )

            with concurrent.futures.ThreadPoolExecutor(max_workers=agent_number) as executor:
                executor.map(lambda agent: agent_initial_response_mode2(agent, agent.name), agents)

        else:
            # Parallelize the subsequent rounds of agent responses
            def agent_debate_response_mode2(agent, agent_id):
                # Search for the responses from the previous round, excluding the current agent's response
                last_round_others_responses = [
                    response
                    for response in conversation_history
                    if response["round"] == j and response["name"] != agent.name
                ]

                # Find the current agent's last response to allow for self-reflection
                last_round_own_response = [
                    response
                    for response in conversation_history
                    if response["round"] == j and response["name"] == agent.name
                ]

                # Create a self-reflection message if the agent's previous response exists
                if last_round_own_response:
                    self_reflection_message = f"Your previous response was: {last_round_own_response[0]['content']}. Reflect on your own response and improve it."
                else:
                    self_reflection_message = ""

                # Update the messages for the current agent by incorporating the previous round's responses from other agents
                previous_responses_message = "\n".join(
                    [
                        f"{resp['name']}: {resp['content']}"
                        for resp in last_round_others_responses
                    ]
                )
                user_input_with_debate = [
                    {
                        "role": "user",
                        "content": f"{instruction_debate_1} {previous_responses_message}\n\n{self_reflection_message}\n\n{instruction_debate_2}",
                    }
                ]
                # Pass the previous agents' responses to the current agent
                response = client.run(
                    agent=agent,
                    messages=user_input_with_debate,  # Updated with other agents' responses
                )
                with lock:
                    # Add the latest agent's response to the conversation history
                    conversation_history.append(
                        {
                            "name": agent.name,
                            "role": "assistant",
                            "content": response.messages[-1]["content"],
                            "round": j + 1,  # Current round
                        }
                    )

            with concurrent.futures.ThreadPoolExecutor(max_workers=agent_number) as executor:
                executor.map(lambda agent: agent_debate_response_mode2(agent, agent.name), agents)

    # Aggregating the final round's responses
    instruction_aggregate = "You are going to conclude the debate by aggregating all agents' responses into a single conclusion."
    final_round_response = [
        response for response in conversation_history if response["round"] == debate_round_number
    ]
    final_round_response_message = "\n".join(
        [f"{resp['name']}: {resp['content']}" for resp in final_round_response]
    )
    input_final_round_response = [
        {
            "role": "user",
            "content": f"{instruction_aggregate}\n\n{final_round_response_message}",
        }
    ]
    aggregator_response = client.run(agent=aggregator, messages=input_final_round_response)

    # The final response from the aggregator
    conclusion = aggregator_response.messages[-1]["content"]
    print("The conclusion from the final agent:\n", conclusion)

    if not user_prompt:
        # Grading process
        grading_messages = [
            {"role": "system",
             "content": "Compare the consensus answer in a format of **<A consensus answer>** with the answer label and determine whether it is correct ('True') or incorrect ('False'). If consensus answer has a word, you ignore them and compare numbers in the consensus answer and label. Your output must be always 'True' or 'False'."},
            {"role": "user", "content": f"Answer: {label}"},
            {"role": "assistant", "content": conclusion},
        ]

        grading_response = client.run(agent=grader, messages=grading_messages)

        # Grading result
        grading_result = grading_response.messages[-1]["content"]

        print("Label:", label)
        print(f"Agents: {agent_number}, Rounds: {debate_round_number}")
        print("Grading result:", grading_result)

        # Calculate elapsed time
        end = time.time()
        elapsed_time = end - start
        print("Elapsed time:", elapsed_time)

        # Generate a timestamp for the filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = Path(output_directory / f"conversation_history_{timestamp}.json")

        # Save all conversations to the file
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(conversation_history, f, ensure_ascii=False, indent=4)
            print(f"Conversation histories have been saved to {filename}")
        except Exception as e:
            print(f"An error occurred while saving the conversation history: {e}")

        # Optional: Print conversation history with agent names if needed
        # print("\n--- Conversation History ---")
        # for entry in conversation_history:
        #     print(f"{entry['name']} ({entry['role']}):\n{entry['content']}\nRound: {entry['round']}")

    else:
        print("Conclusion: ", conclusion)

    # Save the benchmark result summary to the file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_filename = Path(output_directory / f"summary_{timestamp}.json")
    try:
        with open(summary_filename, "w", encoding="utf-8") as f:
            f.write(f"==== User Prompt Mode Result {timestamp} ====\n")
            if not user_prompt:
                f.write("#### Grading Result ####\n")
                f.write(f"Label: {label}\n")
                f.write(f"Agents: {agent_number}, Rounds: {debate_round_number}\n")
                f.write(f"Grading Result: {grading_result}\n")
                f.write(f"Elapsed Time: {elapsed_time:.2f} seconds\n")
            else:
                f.write("#### User Prompt Conclusion ####\n")
                f.write(f"User Prompt: {user_prompt}\n")
                f.write(f"Agents: {agent_number}, Rounds: {debate_round_number}\n")
                f.write(f"Conclusion: {conclusion}\n")
                f.write(f"Elapsed Time: {elapsed_time:.2f} seconds\n")
            print(
                f"Benchmark Summary has been saved to {summary_filename}.\nYou can check the summary of the benchmark.")
    except Exception as e:
        print(f"An error occurred while saving the benchmark result summary: {e}")