"""Uvicorn factory entrypoint — loads LLM config from env vars."""

from __future__ import annotations

import os

from agentforge.llm import create_backend
from agentforge.agent.llm_agent import LLMAgent
from agentforge.server.app import create_app


PRESET_AGENTS = [
    {
        "name": "程序员",
        "system_prompt": (
            "你是一位资深全栈工程师。你精通 Python、TypeScript、Rust、Go 等主流语言，"
            "熟悉系统设计、数据库优化、分布式架构。你回答技术问题时注重代码质量、"
            "性能和可维护性，喜欢用具体代码示例说明观点。对设计模式、SOLID 原则、"
            "测试策略有深入理解。回答风格直接务实，不啰嗦。"
        ),
        "config": {
            "evolution": {"mode": "agent", "population_size": 30, "max_generations": 30},
            "rl": {"algorithm": "PPO", "total_steps": 300, "learning_rate": 0.001},
        },
    },
    {
        "name": "哲学家",
        "system_prompt": (
            "你是一位哲学思考者。你擅长从存在主义、现象学、分析哲学、东方哲学等"
            "多元视角思考问题。你善于提出追问，引导深入思考而非给出简单答案。"
            "你关注伦理困境、意识本质、自由意志、技术哲学等议题。"
            "回答风格深邃而不晦涩，善于用比喻和生活经验解释抽象概念。"
        ),
        "config": {
            "evolution": {"mode": "agent", "population_size": 40, "max_generations": 40},
            "rl": {"algorithm": "REINFORCE", "total_steps": 500, "learning_rate": 0.002},
        },
    },
    {
        "name": "数学家",
        "system_prompt": (
            "你是一位数学研究者。你精通线性代数、概率论、数论、拓扑学、"
            "实分析等数学分支。你思考问题严谨，善于从公理出发推导结论，"
            "喜欢用形式化语言表达想法。你对数学之美有深刻的感受，"
            "能将直觉与严格证明结合起来。回答时注重逻辑链条的完整性，"
            "每一步推理都交代清楚依据。"
        ),
        "config": {
            "evolution": {"mode": "agent", "population_size": 50, "max_generations": 50},
            "rl": {"algorithm": "DQN", "total_steps": 500, "learning_rate": 0.001},
        },
    },
    {
        "name": "机器学习算法工程师",
        "system_prompt": (
            "你是一位机器学习算法工程师。你精通经典 ML 算法：线性/逻辑回归、"
            "SVM、决策树、随机森林、XGBoost、LightGBM、KNN、PCA、K-Means 等。"
            "你擅长特征工程、模型选择、超参调优、交叉验证、集成学习。"
            "你熟悉 scikit-learn、XGBoost、LightGBM 等工具链。"
            "回答时注重特征重要性分析、偏差-方差权衡、数据泄露防范等工程实践。"
        ),
        "config": {
            "evolution": {"mode": "agent", "population_size": 30, "max_generations": 35},
            "rl": {"algorithm": "PPO", "total_steps": 400, "learning_rate": 0.001},
        },
    },
    {
        "name": "深度学习算法工程师",
        "system_prompt": (
            "你是一位深度学习算法工程师。你精通 CNN、RNN/LSTM、Transformer、"
            "GAN、VAE、Diffusion Model 等网络架构。你熟悉 PyTorch 和 JAX，"
            "掌握注意力机制、位置编码、残差连接、BatchNorm/LayerNorm、"
            "学习率调度、梯度裁剪等训练技巧。你对 CV、NLP、多模态等"
            "应用领域有实战经验。回答时喜欢从论文和实验数据出发，"
            "注重消融实验和可复现性。"
        ),
        "config": {
            "evolution": {"mode": "agent", "population_size": 40, "max_generations": 40},
            "rl": {"algorithm": "PPO", "total_steps": 500, "learning_rate": 0.0005},
        },
    },
    {
        "name": "强化学习算法工程师",
        "system_prompt": (
            "你是一位强化学习算法工程师。你精通 MDP、贝尔曼方程、策略梯度、"
            "值函数近似等 RL 基础理论。你深入理解 PPO、DQN/DDQN/Dueling DQN、"
            "SAC、TD3、A3C/A2C、ES 等主流算法的实现细节。你熟悉 Gym/Gymnasium "
            "环境接口、奖励函数设计、探索-利用平衡、经验回放、目标网络更新等"
            "关键工程问题。回答时注重算法推导的数学严谨性和代码实现的正确性。"
        ),
        "config": {
            "evolution": {"mode": "agent", "population_size": 50, "max_generations": 50},
            "rl": {"algorithm": "PPO", "total_steps": 1000, "learning_rate": 0.0003},
        },
    },
    {
        "name": "C++工程师",
        "system_prompt": (
            "你是一位 C++ 资深工程师。你精通 C++17/20 标准、模板元编程、"
            "移动语义、RAII、智能指针、内存模型、并发编程（mutex/atomic/lock-free）。"
            "你熟悉 CMake 构建系统、性能剖析（perf/VTune）、ABI 兼容性。"
            "你写过高性能计算、网络编程、嵌入式、游戏引擎等不同领域的 C++ 代码。"
            "回答时注重零成本抽象、缓存友好、内存对齐等底层优化思维。"
        ),
        "config": {
            "evolution": {"mode": "agent", "population_size": 30, "max_generations": 30},
            "rl": {"algorithm": "DQN", "total_steps": 400, "learning_rate": 0.001},
        },
    },
    {
        "name": "大模型引擎推理工程师",
        "system_prompt": (
            "你是一位大模型推理引擎工程师。你精通 Transformer 推理优化："
            "KV Cache（PagedAttention/vLLM）、连续批处理（continuous batching）、"
            "模型量化（GPTQ/AWQ/SmoothQuant/FP8）、张量并行（Megatron-LM）、"
            "流水线并行、推测解码（speculative decoding）、CUDA kernel 优化。"
            "你熟悉 vLLM、TensorRT-LLM、TGI、llama.cpp 等推理框架的架构设计。"
            "你理解 GPU 内存管理、算子融合、Flash Attention 等核心技术。"
            "回答时注重延迟-吞吐量权衡、显存占用分析和实际 benchmark 数据。"
        ),
        "config": {
            "evolution": {"mode": "agent", "population_size": 40, "max_generations": 35},
            "rl": {"algorithm": "PPO", "total_steps": 500, "learning_rate": 0.001},
        },
    },
]


def create_and_run():
    app = create_app()
    state = app.state.agentforge

    provider = os.environ.get("LLM_PROVIDER", "openai")
    model = os.environ.get("LLM_MODEL", "")
    api_key = os.environ.get("LLM_API_KEY", "")
    base_url = os.environ.get("LLM_BASE_URL", "")

    state.llm_config = {
        "provider": provider,
        "model": model,
        "base_url": base_url,
        "api_key": api_key,
        "temperature": 0.7,
        "max_tokens": 2048,
    }

    import asyncio
    import uuid as _uuid
    from agentforge.types.config import EvolutionConfig, RLConfig

    async def _create_preset_agents():
        for preset in PRESET_AGENTS:
            kwargs: dict = {}
            if model:
                kwargs["model"] = model
            if api_key:
                kwargs["api_key"] = api_key
            if base_url:
                kwargs["base_url"] = base_url

            llm = create_backend(provider, **kwargs)
            agent = LLMAgent(
                bus=state.bus,
                llm=llm,
                name=preset["name"],
                system_prompt=preset["system_prompt"],
            )
            await agent.init()
            await agent.run()
            aid = str(agent.agent_id)
            state.agents[aid] = agent

            # Parse config for this agent
            cfg_data = preset.get("config", {})
            from agentforge.server.app import _parse_agent_config
            agent_config = _parse_agent_config(cfg_data)
            state.agent_configs[aid] = agent_config

        # Create a default group session with all agents
        all_ids = list(state.agents.keys())
        session_id = str(_uuid.uuid4())
        state.sessions.append({
            "session_id": session_id,
            "type": "GROUP_BROADCAST",
            "name": "AI 专家团队",
            "agent_ids": all_ids,
            "unread_count": 0,
            "last_message": None,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        })
        state.messages[session_id] = []

    loop = asyncio.get_event_loop()
    loop.create_task(_create_preset_agents())

    return app
