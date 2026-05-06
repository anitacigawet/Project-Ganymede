# Project Ganymede: Core Architecture & UI Framework

## 1. The Core Philosophy
**Project Ganymede** is the ultimate, open-ended observatory for strategic physics. All commercial SaaS, Think Tank, and FBA-specific constraints have been stripped away. 
* **The Backend:** The **9D-Chess Engine**. A raw, universal theoretical physics engine that calculates multidimensional math, hidden gravity wells, and structural traps across any domain.
* **The Frontend:** **Project Ganymede**. A clean, enterprise-grade React/Next.js wrapper. It is a blank canvas where a user inputs any scenario and watches the physics engine map the topology in real-time.

---

## 2. UI Layout & User Experience (UX)

The platform operates on a stark, minimalist, dark-theme split-screen architecture.

### Left Panel: The Analyst (Context & Logic)
* **Function:** A conversational chat interface.
* **Behavior:** The user types a scenario. The wrapper queries the backend (NotebookLM/Gemini logic) and streams the theoretical breakdown, identifying invisible dimensions and potential Set of Disadvantageous States (SDS).

### Right Panel: The Physics Engine (Interactive 3D Canvas)
* **Function:** A dynamic, interactive React widget rendering the strategic topology.
* **Behavior:** This panel listens to the JSON output from the backend and visually renders the topological traps, gravity wells, and decision nodes matching the current scenario on the Left Panel.

---

## 3. The Default State: The Universal Gravity Well
Before a user inputs a specific scenario, the Right Panel must display a mesmerizing, abstract simulation that visually explains the concept of a "Dimensional Trap." This serves as the technical flex and the visual hook.

**Prompt for the Dynamic Component Generation (For Coder Agent Reference):**
```text
An interactive 3D topological simulation of a universal 'Strategic Gravity Well' (SDS) for the Project Ganymede homepage.

Objective: Allow the user to manipulate abstract strategic variables to watch how a flat landscape warps into an inescapable trap.

Data State: Initialize with a neutral, flat 3D topological grid (representing a stable strategic environment) with several glowing nodes (representing entities or decisions) resting on the surface.

Strategy: 3D Scene layout utilizing a manipulatable topological surface and basic physics.

Inputs: 
1. A 'Dimensional Blindness' slider (0% to 100%).
2. A 'Strategic Stress/Leverage' slider (Low to High).
3. A 'Reset Topology' button.

Behavior: 
Render the 3D grid and nodes. As the user increases the 'Strategic Stress' slider, visually warp the center of the grid downward, carving a deep 'Gravity Well'. Nodes that fall within the warped radius should physically slide down into the center. 
If the user increases the 'Dimensional Blindness' slider, visually fade out or remove connecting grid lines, representing the loss of multi-dimensional awareness, causing nodes to behave more erratically and fall into the well faster. 
Include a dynamic, minimalist data readout panel displaying: 'Topological Stability: [%]', 'SDS Risk Factor: [Low/Critical]', and 'Active Dimensions Mapped: [9 to 1]'. Ensure a sleek, enterprise-grade, dark-theme analytical UI.
```

---

## 4. Development Milestones for Coder Agent (Claude)
1. **Scaffold the App:** Initialize a Next.js/React project with a dark-mode tailwind configuration.
2. **Build the Layout:** Create the split-screen `AnalystPanel` (left) and `PhysicsPanel` (right).
3. **Implement the Default 3D Canvas:** Use `Three.js` or `@react-three/fiber` to build the "Universal Gravity Well" based on the prompt provided above. Ensure the sliders actively manipulate the 3D mesh (the topological grid) in real-time.
4. **Prepare the API Hooks:** Create dummy API endpoints to simulate the flow of a user submitting a scenario, receiving text on the left, and triggering a new 3D mesh state on the right.
