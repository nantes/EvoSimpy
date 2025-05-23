# EvoSimPy - A Simple 2D Evolution Simulator

EvoSimPy is an agent-based life simulation where entities evolve in a 2D grid world. They search for food, consume energy, reproduce, and pass on their genes (with potential mutations) to offspring. This demonstrates basic principles of natural selection and evolution.

## Features

*   **2D Grid World**: Entities move and interact on a configurable grid.
*   **Entities with Genes**:
    *   `speed`: Affects how many cells an entity can move per day.
    *   `feeding_efficiency`: How much energy is gained from food.
    *   `base_longevity`: Potential lifespan.
    *   `reproduction_rate`: Likelihood of attempting reproduction.
    *   `perception_radius`: How far an entity can "see" food (added feature).
*   **Energy Dynamics**: Entities gain energy from food and expend it for daily survival, movement, and reproduction.
*   **Reproduction & Inheritance**: Entities near each other can reproduce, passing a mix of their genes to offspring.
*   **Mutation**: Genes can randomly mutate, introducing variation.
*   **Food Spawning**: Food appears randomly in the environment.
*   **Pygame Visualization**: Real-time graphical display of the simulation.
*   **Configurable Parameters**: Many aspects of the simulation can be tweaked via a configuration dictionary.

## Requirements

*   Python 3.x
*   Pygame: `pip install pygame`

## How to Run

1.  Ensure you have Python and Pygame installed.
2.  Clone this repository or download the `evosim.py` (or similarly named main Python file).
3.  Run the script from your terminal: `python evosim.py`

## Configuration

The main simulation parameters are defined in the `CONFIG` dictionary at the top of the `evosim.py` file. You can adjust these values to experiment:

*   **Grid & Display**: `MAP_WIDTH`, `MAP_HEIGHT`, `CELL_SIZE`, `FPS`.
*   **Population**: `INITIAL_POPULATION`, `MAX_POPULATION`.
*   **Energy**: `INITIAL_ENERGY_MIN/MAX`, `ENERGY_PER_FOOD`, `DAILY_ENERGY_COST`, `MOVE_ENERGY_COST_FACTOR`, `REPRODUCTION_ENERGY_COST`, `MIN_ENERGY_REPRODUCE`.
*   **Food**: `INITIAL_FOOD_ITEMS`, `FOOD_SPAWN_RATE_PER_DAY`, `MAX_FOOD_ON_MAP`.
*   **Reproduction & Genes**: `MIN_REPRODUCTION_AGE`, `MAX_REPRODUCTION_AGE`, `REPRODUCTION_COOLDOWN`, `GENE_MUTATION_PROBABILITY`, `GENE_MUTATION_MAGNITUDE`, and gene-specific ranges (`GENES_BASE`).
*   **Simulation**: `SIM_DAYS_PER_PYGAME_SECOND` (controls simulation speed), `PRINT_SUMMARY_EVERY_N_DAYS`.

## Genes Explained

*   `speed`: Max cells moved per turn. Higher speed costs more energy per move.
*   `feeding_efficiency`: Multiplier for energy gained from food.
*   `base_longevity`: Base maximum age in days.
*   `reproduction_rate`: Innate probability to attempt reproduction if conditions are met.
*   `perception_radius`: How many cells away an entity can detect food.

## Future Enhancements (Ideas)

*   Predator-prey dynamics.
*   More complex environmental factors (e.g., seasons, terrain types).
*   More sophisticated AI for entity behavior (e.g., flocking, better pathfinding).
*   Ability to save/load simulation state.
*   Graphs of population statistics over time.
