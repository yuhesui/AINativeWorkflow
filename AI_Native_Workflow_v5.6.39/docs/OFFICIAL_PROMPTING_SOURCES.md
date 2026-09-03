# Official prompting sources used for the current GPT-5.6 continuation prompt

Updated 2026-08-31. External documentation may change.

Primary current OpenAI sources:

- **GPT-5.6 model guidance / prompting best practices**  
  https://developers.openai.com/api/docs/guides/latest-model  
  Relevant guidance used here: favor leaner prompts; state each important instruction once; provide domain context, hard constraints, approval boundaries, and success criteria; GPT-5.6 can infer more of the execution path; Pro mode is intended for difficult quality-first work.

- **OpenAI Help Center — How do I create a good prompt for an AI model?**  
  https://help.openai.com/en/articles/4936848  
  Relevant guidance used here: make the task clear and specific, provide necessary context, right-size complex work, and use goal-driven language.

- **OpenAI Help Center — Prompt engineering best practices for ChatGPT**  
  https://help.openai.com/en/articles/10032626-how-do-i-prompt-chatgpt-effectively  
  Relevant guidance used here: clear/specific instructions and iterative refinement.

The continuation prompt therefore uses one outcome-oriented contract rather than a large numbered micro-prompt stack. It states package authority, scope, success criteria, autonomy boundaries, required artifacts, and scientific integrity constraints, while leaving ordinary execution decisions to GPT-5.6 Pro.

It does not request visible chain-of-thought. Durable decisions and evidence must be written to the package rather than relying on chat memory.
