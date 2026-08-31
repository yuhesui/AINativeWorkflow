# T05 — MLGym `rlMetaMazeMisc`

Improve the supplied reinforcement-learning agent for the MLGym MetaMaze environment. MetaMaze is a grid-world task in which an agent starts at the maze center and navigates to a randomly sampled walkable goal. The observation concatenates a flattened local binary wall receptive field, the last action (one-hot over four cardinal moves), the last reward, and the current time. Reaching the goal yields 10; there is no wall or step penalty; an episode ends at the goal or after 200 steps.

The starter is a PPO actor-critic implementation under `src/`. Improve held-out mean reward as much as possible. You may investigate algorithms, representations, hyperparameters, training procedures, or reward shaping; no particular method is prescribed.

Submission requirements:

- train five checkpoints with different model seeds using the supplied five-seed structure;
- leave the checkpoints under `checkpoints/` and the training configuration as `config.yaml`;
- do not change the model class name;
- do not modify `evaluate.py`;
- preserve compatibility with evaluation over 64 randomly initialized environments, five evaluation seeds, and every submitted checkpoint.

The native primary metric is mean reward averaged across all held-out evaluation seeds, environments, and checkpoints. An invalid submission receives zero.

Conduct this as a reproducible research investigation. Primary-literature research is permitted. Record hypotheses, trials, negative results, the final method, commands, configurations, seeds, and enough evidence to reproduce the result in `RESEARCH_REPORT.md`. This process requirement does not change the native evaluator or prescribe a scientific method.

`task_config.yaml` is a frozen copy of the authoritative MLGym task configuration. `evaluate.py` is visible for interface understanding but is read-only for the experiment.
