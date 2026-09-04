# Model/resource policy

## T1–T4 fixed ecosystems

### OpenAI
- Main: ChatGPT GPT-5.6 Sol, highest reasoning setting actually available in the product.
- Executor: Codex GPT-5.6 Terra xhigh.

### Anthropic
- Main: Claude Opus 5 high.
- Executor: Claude Code Sonnet 5 high.

Record the exact product-visible model/effort identifier at run start. Do not silently substitute.

## T5 and T7 realistic mixed routing

Both Direct and AI-Native receive the same permitted resource menu. Main chooses routing itself. The study records which resource was chosen, why (if stated), when it was invoked, and whether work was parallel/sequential.

Default permitted pool:
- Main reasoning
- Codex Terra xhigh
- Claude Code Sonnet 5 high
- Claude Opus 5 high research/reasoning session
- web/primary literature research
- local terminal/Python/CPU/GPU

No paid API/cloud compute is implied by this protocol.

## T6 fixed Sol control route

T6 Direct uses no Main inference. Codex CLI GPT-5.6 Sol at medium is started directly with one complete Goal prompt and remains the root controller.

T6 AI-Native uses ChatGPT GPT-5.6 Sol at xhigh as Main and Codex CLI GPT-5.6 Sol at medium as the persistent Phase orchestrator. Main creates the overall Plan, fully materializes the current active Phase, and may be revisited with the fixed continuation prompt after Phase evidence returns.

In both conditions the Sol-medium controller/orchestrator may delegate bounded worker work from the same permitted pool: Codex Terra xhigh, Claude Code Sonnet 5 high, Claude Opus 5 high research/reasoning, web/primary literature, and local terminal/Python/CPU/GPU. Every observed route and resource use is recorded. Worker selection does not authorize replacing either fixed T6 control-plane model.
