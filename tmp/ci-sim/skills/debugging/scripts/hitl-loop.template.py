#!/usr/bin/env python3
"""Human-in-the-loop reproduction loop.

Copy this file, edit the steps below, and run it.
The agent runs the script; the user follows prompts in their terminal.

Usage:
  python hitl-loop.template.py

Two helpers:
  step("<instruction>")          -> show instruction, wait for Enter
  capture("<var_name>", "<question>") -> show question, read response into VAR

At the end, captured values are printed as KEY=VALUE for the agent to parse.
"""
import getpass


def step(instruction):
    print(f"\n>>> {instruction}")
    input("    [Enter when done] ")


def capture(var_name, question):
    print(f"\n>>> {question}")
    answer = input("    > ")
    globals()[var_name] = answer
    return answer


# --- edit below ---------------------------------------------------------

step("Open the app at http://localhost:3000 and sign in.")

capture("ERRORED", "Click the 'Export' button. Did it throw an error? (y/n)")

capture("ERROR_MSG", "Paste the error message (or 'none'):")

# --- edit above ---------------------------------------------------------

print("\n--- Captured ---")
print(f"ERRORED={globals().get('ERRORED', '')}")
print(f"ERROR_MSG={globals().get('ERROR_MSG', '')}")
