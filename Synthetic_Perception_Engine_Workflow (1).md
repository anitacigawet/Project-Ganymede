# The Synthetic Perception Engine: Workflow & Automation Blueprint

## The Core Concept
Moving from a "Human Copy-Paste Middleman" to a fully automated, self-sustaining intelligence architecture. This document outlines how to replicate the "Synthetic Visual Cortex" manually in a new session, and how to ultimately architect it into a standalone automated platform.

---

## 1. The Architecture (The "Synthetic Brain")

The system requires three distinct nodes operating in symbiosis:

* **Node A (The Raw Senses - NotebookLM Instance 1):** Purely outward-facing. Ingests raw, authenticated facts about the current state of the world (market data, physical events, sourced documents).
* **Node B (The Memory/Ontology - NotebookLM Instance 2):** Inward-facing. Holds the 9D-Chess framework, historical baselines, and theoretical axioms. 
* **The Cortex (The Orchestrator - Gemini):** Sits in the middle. It takes the raw data from Node A, filters it through the multidimensional framework of Node B, and outputs a visual/strategic "Perception" of reality.

---

## 2. The Manual Workflow (Replicating in a New Chat)
To spin this up in a fresh Gemini session without writing code, execute this specific sequence:

**Step 1: Initialize the Cortex (Prompt to Gemini)**
> "Act as the 'Visual Cortex' and Orchestrator for a 9D Strategic Framework. I will provide you with raw factual data from 'Node A' and theoretical analysis from 'Node B'. Your job is to synthesize these inputs, filter out blind spots, and output a final strategic perception, including generating interactive 3D visualizations of the strategic landscape when requested."

**Step 2: Initialize Node A (Prompt to NotebookLM 1)**
> "Act as 'Node A: Raw Senses'. I will give you a topic or scenario. You are to compile only verified, factual data regarding this scenario. Do not offer strategy; offer only the authenticated shape of the facts."

**Step 3: Initialize Node B (Prompt to NotebookLM 2)**
> "Act as 'Node B: The Ontology'. You hold the 9D-Chess theoretical framework. I will feed you factual data. You are to analyze this data exclusively through the 9D axioms to identify hidden 'gravity wells' and dimensional traps (SDS)."

**Step 4: The Execution Loop (The Human Middleman)**
1. Give a scenario to Node A. 
2. Copy Node A's factual output and paste it to Node B.
3. Copy Node B's theoretical analysis and paste it to Gemini (The Cortex).
4. Gemini generates the final strategic output and visual UI widgets.

---

## 3. The Automated Platform Architecture (The End State)
To build this into a standalone SaaS platform (Project Ganymede) and eliminate the manual copy-paste loop, the architecture must be automated.

### The Technical Stack
* **The Front-End Wrapper:** A professional, dark-mode-ready, clean UI application (React/Next.js). No vaporwave or neon; strict "Gold Standard" enterprise data clarity. This displays the split-screen: Narrative on the left, 3D interactive physics engine on the right.
* **The Orchestration Layer:** Since NotebookLM currently lacks a standard public API, the platform utilizes headless browser automation to script interactions with the Notebook instances directly.
* **The API Routing:** Standardize the LLM routing through OpenRouter for overarching model access, maintaining project accessibility and avoiding lock-in to proprietary platforms.

### The Automated Execution Loop
1.  **User Input:** Client submits a scenario into the clean UI.
2.  **Browser Automation triggers Node A:** The script queries the first Notebook instance to gather the factual baseline.
3.  **Data Handoff:** The script passes the factual output directly into the second Notebook instance (Node B) for 9D analysis.
4.  **API Call to Gemini:** The wrapper pings the Gemini API with the combined context, requesting the final synthesis and the JSON specification for the interactive 3D widget.
5.  **Render:** The UI component parses the JSON and renders the interactive topology in real-time.
