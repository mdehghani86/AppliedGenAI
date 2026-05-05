# Generative AI Course
> **Comprehensive Learning Path** - Hands-on course covering modern generative AI techniques and applications

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square)
![OpenAI](https://img.shields.io/badge/OpenAI-API-blue?style=flat-square)
![LangChain](https://img.shields.io/badge/LangChain-Framework-blue?style=flat-square)

---

## 🎯 Course Overview

**Practical AI Development Training**

This course transforms AI learning from theoretical concepts into practical expertise. The comprehensive curriculum covers prompt engineering, LangChain, RAG systems, and multi-agent architectures—all while building real applications and understanding industry best practices.

---

## 📚 Core Modules

| Module | Topic | Description |
|--------|-------|-------------|
| **M3** | **Prompting Strategies** | Advanced prompt engineering and optimization techniques |
| **M4** | **GenAI Applications** | Real-world AI triage systems and interactive applications |
| **M5** | **LangChain Framework** | Templates, memory management, and chain composition |
| **M6** | **AI Agents** | Autonomous agents with tool integration and coordination |
| **M8** | **RAG Systems** | Retrieval-Augmented Generation with vector databases |
| **M10** | **Advanced Topics** | LangGraph workflows and complex AI architectures |
| **M11** | **Multi-Agent Systems** | CrewAI framework and investment analysis agents |

### 🔬 Specialized Labs
- **Health AI Lab** - Medical applications of large language models
- **API Integration** - ChatGPT API mastery and custom prompt development

---

## 🛠️ Technology Stack

```
Python • OpenAI API • LangChain • LangGraph • CrewAI • Vector Databases • Jupyter Notebooks
```

---

## 🚀 Quick Start

Every lab runs in **Google Colab** out of the box. Open any `.ipynb`, click *Open in Colab*, and:

1. **Set the API key once.** In Colab → 🔑 sidebar → add a secret named exactly `OPENAI_API_KEY` and toggle *Notebook access* ON. Every lab uses the same name, so you set it once.
2. **Run the first (setup) cell.** It downloads `utils.py`, loads your key, pings OpenAI to confirm the key works (✅ / ❌), and pins a sticky lab-name pill at the top of the page so you always know which notebook you're in.
3. **Continue with the lab.**

### Shared utilities (`utils.py`)

| Symbol | Purpose |
|---|---|
| `pretty_print(text, title, theme)` | Styled HTML message boxes (themes: blue, red, yellow, green, gray) |
| `DEFAULT_CHAT_MODEL` | Default reasoning model (currently `gpt-5`) — change it once, everywhere |
| `DEFAULT_MINI_MODEL` | Cheaper / faster default (currently `gpt-5-mini`) |
| `DEFAULT_EMBED_MODEL` | Default embeddings model (currently `text-embedding-3-small`) |
| `get_openai_key(verify=True)` | Reads `OPENAI_API_KEY` from Colab secret → env var → prompt; verifies |
| `verify_openai_key()` | Standalone API-key health check |
| `lab_pill(title)` | Sticky pill banner at top of notebook |

> **📌 Models update fast.** Every lab references `DEFAULT_CHAT_MODEL` rather than a hardcoded model string. To upgrade the whole course to a newer LLM, change one constant in `utils.py`. Students are welcome (and encouraged) to swap to any newer OpenAI / Anthropic / Google model they have access to.

---

## 🎓 Learning Outcomes

**Upon completion, you'll master:**

✅ Advanced prompt engineering and optimization  
✅ Building production-ready AI applications  
✅ Implementing RAG systems for knowledge integration  
✅ Developing autonomous AI agents  
✅ Creating multi-agent collaborative systems  
✅ API integration and deployment strategies  

---

## 📁 Repository Structure

```
📦 generative-ai-course
├── 📓 M3_Lab1_Prompting_Strategies.ipynb
├── 📓 M4_Lab1_GenAI_Triage.ipynb
├── 📓 M4_Lab2_GenAI_BeerGame_V1.ipynb
├── 📓 M5_Lab1_LangChain_LLMs.ipynb
├── 📓 M5_Lab2_LangChain_Templates_Memory.ipynb
├── 📓 M6_Lab1_AI_Agents.ipynb
├── 📓 M6_Lab2_AI_Agents_Applications.ipynb
├── 📓 M8_Lab1_RAG.ipynb
├── 📓 M10_Lab1_LangGraph_Intro.ipynb
├── 📓 M11_Lab1_CrewAI.ipynb
├── 📓 M11_Lab2_Multi_Agent_Investment_Analysis.ipynb
├── 📓 Lab_7_HealthLLM.ipynb
├── 📓 ChatGPT_API_Tutorial.ipynb
├── 📓 Prompting_with_API.ipynb
└── 📄 README.md
```

---

<div align="center">

**Built for the future of AI development**

[![Course](https://img.shields.io/badge/Course-Generative%20AI-blue?style=for-the-badge)](.)
[![Labs](https://img.shields.io/badge/Labs-15+-blue?style=for-the-badge)](.)
[![Duration](https://img.shields.io/badge/Duration-5%20Months-blue?style=for-the-badge)](.)

</div>
