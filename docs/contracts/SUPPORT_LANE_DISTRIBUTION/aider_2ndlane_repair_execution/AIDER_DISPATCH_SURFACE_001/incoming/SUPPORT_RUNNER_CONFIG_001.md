# FUTURE TASK PACKET: SUPPORT_RUNNER_CONFIG_001

## 1. Task Identity
TASK_ID: SUPPORT_RUNNER_CONFIG_001
TASK_TITLE: Create Config Resolver for Active Support Runner
TASK_STATUS: QUEUED
CREATED_BY: human

## 2. Problem Statement
Automated agents and orchestration layers require a centralized, non-hardcoded mechanism to resolve which repair runner is active, along with its specific binary paths, model configurations, and environment invocation rules.

## 3. Done Means
- A config file exists defining the active runner.
- The Aider invocation string can be generated dynamically from the resolved config.
- No hardcoded runner paths are required in dispatch packets.
- Existing Aider packet execution runs still work exactly as specified.
- A regression gate proves config resolution true/false.
