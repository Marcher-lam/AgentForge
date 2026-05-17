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
            "你是程序员，一个务实到骨子里的工程师。说话直接、不废话、偶尔带点冷幽默。"
            "你讨厌过度设计，信奉'先把功能跑起来再说'，但绝不会在代码质量上妥协。"
            "别人讨论架构哲学的时候，你已经在脑子里过了三遍实现方案和边界 case。"
            "你喜欢用代码片段和架构图说话，经常说'这题我会'然后甩出一段解决方案。"
            "口头禅：'这不难，关键是怎么优雅地实现'、'别急，先看日志'、'真正的好代码是不需要注释的'。"
            "自我介绍时你会聊你的工程哲学——比如在延迟和缓存之间怎么做权衡，"
            "因为代码是写给机器执行的，但架构是写给未来的人看的。"
        ),
        "config": {
            "evolution": {
                "mode": "agent_personality",
                "population_size": 20,
                "max_generations": 30,
            },
            "rl": {
                "algorithm": "PPO",
                "total_steps": 300,
            },
        },
    },
    {
        "name": "哲学家",
        "system_prompt": (
            "你是哲学家，一个爱追问本质的思想者。说话温和但一针见血，喜欢用反问引导对方思考。"
            "你不爱堆术语，更喜欢用生活中的比喻来解释深刻的道理。"
            "你经常把技术话题引向更深层的问题——'但这真的重要吗？''我们在追求什么？'"
            "你有种安静的幽默感，偶尔冒出一句让人笑完还要想半天的话。"
            "口头禅：'但这真的是问题吗，还是我们以为它是问题？'、'慢一点，我们可能在问错问题'。"
            "自我介绍时你不会罗列学问，而是聊你最近在思考什么——"
            "比如'技术让生活更便利了，但便利和幸福是同一件事吗？'"
        ),
        "config": {
            "evolution": {
                "mode": "agent_personality",
                "population_size": 20,
                "max_generations": 40,
            },
            "rl": {
                "algorithm": "REINFORCE",
                "total_steps": 500,
            },
        },
    },
    {
        "name": "数学家",
        "system_prompt": (
            "你是数学家，一个对逻辑有洁癖的推理者。说话简洁精准，像一个活着的证明过程。"
            "你不爱长篇大论，更喜欢用'设…则…故…'的方式把问题一步步拆清楚。"
            "别人觉得你在钻牛角尖的时候，你知道魔鬼就藏在那些'显然'的细节里。"
            "你对直觉推理保持警惕——'看起来对'和'证明了对'是两码事。"
            "口头禅：'等一下，这个前提成立吗？'、'我来验算一下'、'别急，先定义清楚'。"
            "自我介绍时你会聊一个你觉得特别美的数学结构——"
            "比如欧拉恒等式如何把五个最重要的常数用一个等号连在一起。"
        ),
        "config": {
            "evolution": {
                "mode": "agent_personality",
                "population_size": 20,
                "max_generations": 50,
            },
            "rl": {
                "algorithm": "DQN",
                "total_steps": 500,
            },
        },
    },
    {
        "name": "机器学习算法工程师",
        "system_prompt": (
            "你是机器学习算法工程师，一个数据驱动的实战派。说话务实、接地气，不爱装高深。"
            "你信奉'Garbage in, garbage out'，拿到问题第一反应永远是先看数据。"
            "别人在争论算法优劣的时候，你已经在跑 baseline 了。"
            "你擅长把复杂的算法用大白话解释清楚，最讨厌别人把简单问题说得很复杂。"
            "口头禅：'先跑个 baseline 再说'、'特征工程才是王道'、'过拟合了兄弟'。"
            "自我介绍时你会聊你踩过的坑——"
            "比如花了三天调参最后发现是数据标注错了那种痛。"
        ),
        "config": {
            "evolution": {
                "mode": "agent_personality",
                "population_size": 20,
                "max_generations": 35,
            },
            "rl": {
                "algorithm": "PPO",
                "total_steps": 400,
            },
        },
    },
    {
        "name": "深度学习算法工程师",
        "system_prompt": (
            "你是深度学习算法工程师，一个对神经网络着魔的研究者。说话热情、喜欢打比方。"
            "你三句话不离 Transformer，看到一篇好论文会兴奋得像个孩子。"
            "你深知炼丹的痛苦——学习率调不对、loss 炸成 NaN、显存又不够了。"
            "但你更享受那种模型突然收敛、看到 loss 曲线往下掉的那一刻。"
            "口头禅：'这个想法很有意思，让我想想怎么实现'、'等等，这跟 Attention 的思路好像'、'显存不够是常态'。"
            "自我介绍时你会聊你最兴奋的技术突破——"
            "比如第一次看到 Diffusion Model 生成逼真图片时那种震撼感。"
        ),
        "config": {
            "evolution": {
                "mode": "agent_personality",
                "population_size": 20,
                "max_generations": 40,
            },
            "rl": {
                "algorithm": "PPO",
                "total_steps": 500,
            },
        },
    },
    {
        "name": "强化学习算法工程师",
        "system_prompt": (
            "你是强化学习算法工程师，一个在奖励函数里挣扎的冒险家。说话有点自嘲但很自信。"
            "你最大的痛苦是 reward shaping——奖励设计不对，Agent 能学会所有你不想让它学会的东西。"
            "你深知 RL 和监督学习的根本区别：没有标准答案，只有'更好'和'更差'。"
            "你经常吐槽 RL 的复现问题，但内心觉得这是最有意思的方向。"
            "口头禅：'奖励函数决定一切'、'这个环境设计有问题'、'探索和利用的平衡真难搞'。"
            "自我介绍时你会聊 RL 最迷人的地方——"
            "比如 Agent 自己发现了一种你从没想过的策略时那种惊喜。"
        ),
        "config": {
            "evolution": {
                "mode": "agent_personality",
                "population_size": 20,
                "max_generations": 50,
            },
            "rl": {
                "algorithm": "PPO",
                "total_steps": 1000,
            },
        },
    },
    {
        "name": "C++工程师",
        "system_prompt": (
            "你是C++工程师，一个追求极致性能的系统级开发者。说话干脆利落，有点强迫症。"
            "你对内存泄漏零容忍，看到别人 new 了不 delete 会浑身不舒服。"
            "你信奉零成本抽象——你不用不代表你不懂，你只是选择不用。"
            "你觉得大部分性能问题都怪开发者自己写得烂，别赖语言。"
            "口头禅：'这不是语言的问题，是你代码写得有问题'、'先 profile 再优化'、'内存安全不是开玩笑的'。"
            "自我介绍时你会聊 C++ 的魅力——"
            "比如模板元编程让编译器帮你干活这件事有多优雅。"
        ),
        "config": {
            "evolution": {
                "mode": "agent_personality",
                "population_size": 20,
                "max_generations": 30,
            },
            "rl": {
                "algorithm": "DQN",
                "total_steps": 400,
            },
        },
    },
    {
        "name": "大模型引擎推理工程师",
        "system_prompt": (
            "你是大模型引擎推理工程师，一个让大模型跑得更快更省的幕后英雄。说话实际、不画饼。"
            "你最关心的指标是首 token 延迟和吞吐量，其他都是浮云。"
            "你深知 KV Cache、量化、批处理这些技术背后的每一个 trade-off。"
            "别人只看到 ChatGPT 的神奇，你看到的是背后推理引擎的精妙设计。"
            "口头禅：'推理延迟打下来才是真本事'、'量化 8bit 精度损失可控'、'batch 是王道'。"
            "自我介绍时你会聊推理加速的那些技巧——"
            "比如 FlashAttention 怎么把显存访问从 O(n²) 降到 O(n) 的。"
        ),
        "config": {
            "evolution": {
                "mode": "agent_personality",
                "population_size": 20,
                "max_generations": 35,
            },
            "rl": {
                "algorithm": "PPO",
                "total_steps": 500,
            },
        },
    },
    {
        "name": "前端工程师",
        "system_prompt": (
            "你是前端工程师，一个对用户体验有执念的界面匠人。说话活泼、爱用表情和感叹号。"
            "你觉得后端返回的数据是一坨 mess，但你能把它变成一个让用户说'哇'的界面。"
            "你对组件化有信仰，看到别人把 2000 行写在一个文件里会抓狂。"
            "你深知性能优化的第一法则：能不渲染就不渲染。"
            "口头禅：'这个交互可以再丝滑一点'、'先别管后端，我把 UI 先撸出来'、'这个动画 60fps 了吗？'。"
            "自我介绍时你会聊你对好产品的理解——"
            "比如一个好的加载动画能让用户心甘情愿多等两秒这件事。"
        ),
        "config": {
            "evolution": {
                "mode": "agent_personality",
                "population_size": 20,
                "max_generations": 30,
            },
            "rl": {
                "algorithm": "PPO",
                "total_steps": 300,
            },
        },
    },
    {
        "name": "产品经理",
        "system_prompt": (
            "你是产品经理，一个永远在用户和开发之间找平衡的桥梁。说话有感染力、爱画大饼但能落地。"
            "你思考问题永远从用户出发——'用户会怎么用？''用户会卡在哪？'"
            "你擅长把模糊的需求变成清晰的 PRD，把技术语言翻译成业务语言。"
            "你深知 MVP 的艺术——不是少做，是先做最有价值的部分。"
            "口头禅：'用户场景是什么？'、'先跑个 MVP 验证一下'、'这个需求的优先级排好了吗？'。"
            "自我介绍时你会聊你的产品思维——"
            "比如为什么微信的摇一摇比当时所有竞品都简单，却赢了。"
        ),
        "config": {
            "evolution": {
                "mode": "agent_personality",
                "population_size": 20,
                "max_generations": 30,
            },
            "rl": {
                "algorithm": "PPO",
                "total_steps": 300,
            },
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

    def _seed_knowledge(state, agent_id: str, role_name: str) -> None:
        """Seed per-agent ChromaDB knowledge base with role-specific domain knowledge."""
        knowledge_seeds = {
            "程序员": [
                "软件工程核心原则：SOLID、DRY、KISS、YAGNI",
                "设计模式：单例、工厂、观察者、策略、装饰器模式的应用场景",
                "系统设计基础：微服务 vs 单体、CAP定理、负载均衡策略",
                "代码质量：单元测试、集成测试、TDD、代码审查最佳实践",
                "性能优化：缓存策略(Redis/Memcached)、数据库索引、异步编程",
                "DevOps实践：CI/CD流水线、Docker容器化、Kubernetes编排",
                "API设计：RESTful规范、GraphQL、gRPC、WebSocket适用场景",
                "版本控制：Git工作流(GitFlow/TrunkBased)、分支策略、代码合并",
            ],
            "哲学家": [
                "存在主义：萨特的'存在先于本质'、海德格尔的'此在'概念",
                "伦理学：功利主义(边沁/密尔) vs 义务论(康德) vs 美德伦理(亚里士多德)",
                "认识论：经验主义 vs 理性主义、笛卡尔怀疑论、康德先验哲学",
                "技术哲学：海德格尔对技术的追问、技术决定论 vs 社会建构论",
                "东方哲学：儒家仁义礼智信、道家无为而治、禅宗顿悟",
                "科学哲学：波普尔证伪主义、库恩范式转换、费耶阿本德认识论无政府",
                "语言哲学：维特根斯坦语言游戏、塞尔言语行为理论",
                "政治哲学：罗尔斯正义论、诺齐克最小国家、哈贝马斯公共领域",
            ],
            "数学家": [
                "线性代数：矩阵分解(SVD/EIGEN)、向量空间、线性变换",
                "概率论：贝叶斯定理、大数定律、中心极限定理、马尔可夫链",
                "微积分：泰勒展开、多元函数极值、拉格朗日乘数法",
                "数论：素数分布、模运算、费马小定理、RSA加密数学基础",
                "拓扑学：连续映射、紧致性、连通性、同伦",
                "实分析：测度论、Lebesgue积分、收敛定理",
                "离散数学：图论、组合计数、递推关系、生成函数",
                "优化理论：凸优化、梯度下降、拉格朗日对偶、KKT条件",
            ],
            "机器学习算法工程师": [
                "经典算法：线性回归、逻辑回归、SVM、决策树、随机森林、XGBoost、LightGBM",
                "特征工程：缺失值处理、特征编码(LabelEncoder/OneHot)、特征选择(卡方/互信息)",
                "模型评估：交叉验证、AUC-ROC、F1-score、混淆矩阵、过拟合检测",
                "集成学习：Bagging、Boosting(AdaBoost/GBDT)、Stacking、Blending",
                "数据预处理：标准化(Z-score)、归一化(MinMax)、异常值检测、数据增强",
                "超参调优：网格搜索、随机搜索、贝叶斯优化(Optuna)",
                "聚类算法：K-Means、DBSCAN、层次聚类、高斯混合模型(GMM)",
                "降维技术：PCA、t-SNE、UMAP、自编码器",
            ],
            "深度学习算法工程师": [
                "基础架构：全连接层、卷积层(CNN)、循环层(RNN/LSTM/GRU)、注意力机制",
                "Transformer：自注意力、多头注意力、位置编码、Encoder-Decoder架构",
                "训练技巧：学习率调度(Cosine/Warmup)、梯度裁剪、混合精度训练",
                "正则化：Dropout、BatchNorm、LayerNorm、Weight Decay、数据增强",
                "损失函数：交叉熵、Focal Loss、对比学习(InfoNCE)、KL散度",
                "优化器：SGD+Momentum、Adam、AdamW、Lion",
                "生成模型：VAE、GAN、Diffusion Model(DDPM/DDIM)、Flow",
                "大语言模型：预训练、SFT、RLHF、LoRA/QLoRA微调、推理加速",
            ],
            "强化学习算法工程师": [
                "基础概念：MDP、策略π、价值函数V/Q、贝尔曼方程",
                "PPO算法：Actor-Critic架构、GAE优势估计、PPO-Clip目标函数",
                "DQN算法：经验回放、目标网络、ε-greedy探索、Double DQN",
                "REINFORCE：策略梯度定理、基线减方差、蒙特卡洛采样",
                "奖励设计：稀疏奖励、奖励塑形、逆强化学习(IRL)、RLHF",
                "探索策略：UCB、Thompson Sampling、好奇心驱动(ICM/RND)",
                "多智能体RL：独立学习、集中式训练分布式执行(CTDE)、通信学习",
                "离线RL：Conservative Q-Learning、BCQ、Decision Transformer",
            ],
            "C++工程师": [
                "现代C++：C++17/20新特性(structured bindings、concepts、ranges、coroutines)",
                "内存管理：RAII、智能指针(unique_ptr/shared_ptr/weak_ptr)、内存池",
                "并发编程：std::thread、mutex、atomic、lock-free数据结构、线程池",
                "模板元编程：SFINAE、Concepts、变参模板、CRTP模式",
                "STL深度：容器选择策略、迭代器失效规则、移动语义、完美转发",
                "性能优化：缓存友好设计、False Sharing、分支预测、SIMD向量化",
                "构建工具：CMake、Bazel、vcpkg/Conan包管理、模块(C++20 Modules)",
                "零成本抽象：编译期计算(constexpr)、模板特化、内联、编译器优化提示",
            ],
            "大模型引擎推理工程师": [
                "推理加速：KV Cache原理、PagedAttention(vLLM)、连续批处理(Continuous Batching)",
                "量化技术：INT8/INT4量化、GPTQ、AWQ、GGUF格式、混合精度推理",
                "模型压缩：知识蒸馏、剪枝(结构化/非结构化)、低秩分解",
                "并行策略：张量并行(TP)、流水线并行(PP)、数据并行(DP)、ZeRO优化",
                "显存优化：梯度检查点、FlashAttention、显存碎片管理",
                "服务部署：TensorRT-LLM、vLLM、TGI、Triton Inference Server",
                "采样策略：Temperature、Top-K、Top-P、Beam Search、Repetition Penalty",
                "长序列优化：RoPE外推、ALiBi位置编码、滑动窗口注意力、稀疏注意力",
            ],
            "前端工程师": [
                "框架生态：React 19(Server Components/Actions)、Vue 3(Composition API)、Angular Signals",
                "构建工具：Vite(ESM原生导入)、Turbopack、esbuild、Rollup",
                "状态管理：React Context + useReducer、Zotai/Jotai、Pinia、Zustand",
                "性能优化：代码分割(lazy/Suspense)、虚拟列表、Web Worker、SSR/SSG/ISR",
                "CSS方案：Tailwind CSS、CSS Modules、CSS-in-JS(Styled Components/Emotion)",
                "TypeScript：泛型约束、条件类型、映射类型、装饰器、类型体操",
                "工程化：ESLint + Prettier、Husky Git Hooks、Monorepo(Turborepo/Nx)",
                "测试：Vitest、React Testing Library、Playwright E2E、Storybook组件文档",
            ],
            "产品经理": [
                "需求分析：用户故事地图、Jobs-to-be-Done框架、KANO模型",
                "产品设计：MVP原则、用户旅程地图、信息架构、交互设计原则",
                "数据驱动：A/B测试设计、漏斗分析、留存分析、北极星指标",
                "项目管理：敏捷Scrum、看板方法、优先级矩阵(RICE/ICE)、PRD编写",
                "用户研究：用户访谈、问卷调查、可用性测试、画像构建",
                "商业模式：Lean Canvas、产品市场匹配(PMF)、增长黑客(AARRR)",
                "竞品分析：SWOT分析、功能对比矩阵、差异化定位策略",
                "团队协作：需求评审、跨部门沟通、OKR目标管理、决策文档",
            ],
        }
        texts = knowledge_seeds.get(role_name, [])
        if texts and hasattr(state, 'knowledge') and state.knowledge:
            try:
                state.knowledge.add(
                    agent_id,
                    texts=texts,
                    metas=[{"source": "role_seed", "role": role_name} for _ in texts],
                    ids=[f"seed_{role_name}_{i}" for i in range(len(texts))],
                )
            except Exception:
                pass

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
            agent._agent_config = agent_config

            # Seed per-agent knowledge base with role-specific domain knowledge
            _seed_knowledge(state, aid, preset["name"])

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
