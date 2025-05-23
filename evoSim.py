import pygame
import random
import math
import time

# --- SIMULATOR CONFIGURATION ---
CONFIG = {
    # Grid & Display
    "MAP_WIDTH": 50,  # In cells
    "MAP_HEIGHT": 40, # In cells
    "CELL_SIZE": 15,  # In pixels
    "FPS": 10,        # Pygame screen updates per second

    # Colors
    "COLOR_BACKGROUND": (20, 20, 20),
    "COLOR_GRID": (40, 40, 40),
    "COLOR_ENTITY_DEFAULT": (50, 150, 255), # Blueish
    "COLOR_ENTITY_LOW_ENERGY": (255, 100, 50), # Orangish
    "COLOR_FOOD": (50, 200, 50), # Green

    # Population
    "INITIAL_POPULATION": 30,
    "MAX_POPULATION": 150,

    # Energy
    "INITIAL_ENERGY_MIN": 80,
    "INITIAL_ENERGY_MAX": 120,
    "ENERGY_PER_FOOD": 50,
    "DAILY_ENERGY_COST": 2, # Base cost per day for existing
    "MOVE_ENERGY_COST_FACTOR": 0.2, # Energy cost per cell moved (multiplied by speed gene effect)
    "REPRODUCTION_ENERGY_COST": 40,
    "MIN_ENERGY_REPRODUCE": 70,

    # Food
    "INITIAL_FOOD_ITEMS": 60,
    "FOOD_SPAWN_PER_DAY": 8, # How many new food items try to spawn each day
    "MAX_FOOD_ON_MAP": 100,

    # Reproduction and Genes
    "MIN_REPRODUCTION_AGE": 3,  # Days
    "MAX_REPRODUCTION_AGE": 20, # Days
    "REPRODUCTION_COOLDOWN_DAYS": 2, # Minimum days between reproductions for an entity
    "REPRODUCTION_DISTANCE": 2, # Max cell distance for entities to reproduce
    "GENE_MUTATION_PROBABILITY": 0.05, # 5% chance a gene mutates
    "GENE_MUTATION_MAGNITUDE": 0.2,   # Max % change for a mutation

    "GENES_BASE": {
        # name: {min_val, max_val, initial_min, initial_max}
        "speed":                {"min": 0.5, "max": 4.0, "initial_min": 1.0, "initial_max": 2.0}, # Cells per day
        "feeding_efficiency":   {"min": 0.5, "max": 2.0, "initial_min": 0.8, "initial_max": 1.2},
        "base_longevity":       {"min": 10,  "max": 40,  "initial_min": 15,  "initial_max": 25}, # Days
        "reproduction_rate":    {"min": 0.1, "max": 0.9, "initial_min": 0.3, "initial_max": 0.6}, # Prob to try if conditions met
        "perception_radius":    {"min": 1,   "max": 8,   "initial_min": 2,   "initial_max": 4}  # Cells
    },

    # Simulation Flow
    "SIM_DAYS_PER_PYGAME_SECOND": 2, # How many simulation days pass per real second (approx)
    "PRINT_SUMMARY_EVERY_N_DAYS": 20,
    "SHOW_GRID": True,
    "DEBUG_LOGGING": False, # More verbose console output for debugging
}

class Entity:
    _next_id = 0

    def __init__(self, x, y, initial_energy, genes=None):
        self.id = Entity._next_id
        Entity._next_id += 1
        self.x = x
        self.y = y
        self.energy = initial_energy
        self.age = 0
        self.genes = genes if genes else self._generate_random_genes()
        self.is_alive = True
        self.days_since_last_reproduction = CONFIG["REPRODUCTION_COOLDOWN_DAYS"] # Can reproduce immediately

    def _generate_random_genes(self):
        generated_genes = {}
        for name, ranges in CONFIG["GENES_BASE"].items():
            generated_genes[name] = random.uniform(ranges["initial_min"], ranges["initial_max"])
        return generated_genes

    def daily_update(self, game_map):
        if not self.is_alive:
            return

        self.age += 1
        self.energy -= CONFIG["DAILY_ENERGY_COST"]
        self.days_since_last_reproduction += 1

        if self.energy <= 0 or self.age > self.genes["base_longevity"]:
            self.die()
            return

        # Movement and Feeding
        self._move_and_feed(game_map)


    def _move_and_feed(self, game_map):
        if not self.is_alive: return

        target_food_pos = self._perceive_food(game_map)
        
        # Determine number of steps based on speed gene
        # Speed here determines how many *attempts* to move one cell are made, or max distance
        max_steps = int(round(self.genes["speed"]))

        for _ in range(max_steps):
            if not self.is_alive: break # Died from energy cost of previous step

            prev_x, prev_y = self.x, self.y
            
            if target_food_pos:
                # Move towards food
                dx = target_food_pos[0] - self.x
                dy = target_food_pos[1] - self.y
                if dx > 0: self.x += 1
                elif dx < 0: self.x -= 1
                if dy > 0: self.y += 1
                elif dy < 0: self.y -= 1
            else:
                # Random walk
                self.x += random.choice([-1, 0, 1])
                self.y += random.choice([-1, 0, 1])

            # Clamp to map boundaries
            self.x = max(0, min(self.x, CONFIG["MAP_WIDTH"] - 1))
            self.y = max(0, min(self.y, CONFIG["MAP_HEIGHT"] - 1))

            # Energy cost for moving
            if self.x != prev_x or self.y != prev_y:
                # Higher speed gene means more potential moves, but also more cost if actually moving
                move_cost = CONFIG["MOVE_ENERGY_COST_FACTOR"] * (1 + self.genes["speed"] / 2) 
                self.energy -= move_cost
                if self.energy <= 0:
                    self.die()
                    break
            
            # Try to eat if on food
            if game_map.is_food_at(self.x, self.y):
                self.eat(game_map.remove_food(self.x, self.y))
                target_food_pos = None # Stop moving towards this food
                if CONFIG["DEBUG_LOGGING"]: print(f"Entity {self.id} ate at ({self.x},{self.y}). Energy: {self.energy:.1f}")
                break # Stop moving for this day after eating

    def _perceive_food(self, game_map):
        radius = int(round(self.genes["perception_radius"]))
        closest_food = None
        min_dist_sq = float('inf')

        # Check cells within perception radius
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx == 0 and dy == 0: continue # Skip self cell for initial check
                
                check_x, check_y = self.x + dx, self.y + dy
                if 0 <= check_x < CONFIG["MAP_WIDTH"] and 0 <= check_y < CONFIG["MAP_HEIGHT"]:
                    if game_map.is_food_at(check_x, check_y):
                        dist_sq = dx*dx + dy*dy
                        if dist_sq < min_dist_sq:
                            min_dist_sq = dist_sq
                            closest_food = (check_x, check_y)
        return closest_food


    def eat(self, food_amount): # food_amount is notionally 1, but could be variable
        if not self.is_alive: return
        energy_gained = food_amount * CONFIG["ENERGY_PER_FOOD"] * self.genes["feeding_efficiency"]
        self.energy += energy_gained

    def can_reproduce(self):
        return (self.is_alive and
                self.energy >= CONFIG["MIN_ENERGY_REPRODUCE"] and
                CONFIG["MIN_REPRODUCTION_AGE"] <= self.age <= CONFIG["MAX_REPRODUCTION_AGE"] and
                self.days_since_last_reproduction >= CONFIG["REPRODUCTION_COOLDOWN_DAYS"])

    def reproduce(self, partner, child_x, child_y):
        if not self.can_reproduce() or not partner.can_reproduce():
            return None

        self.energy -= CONFIG["REPRODUCTION_ENERGY_COST"]
        partner.energy -= CONFIG["REPRODUCTION_ENERGY_COST"]
        self.days_since_last_reproduction = 0
        partner.days_since_last_reproduction = 0

        child_genes = {}
        for gene_name, ranges in CONFIG["GENES_BASE"].items():
            # Inheritance: randomly pick from one parent
            inherited_value = random.choice([self.genes[gene_name], partner.genes[gene_name]])

            # Mutation
            if random.random() < CONFIG["GENE_MUTATION_PROBABILITY"]:
                mutation = inherited_value * random.uniform(-CONFIG["GENE_MUTATION_MAGNITUDE"], CONFIG["GENE_MUTATION_MAGNITUDE"])
                mutated_value = inherited_value + mutation
                # Clamp to absolute min/max for the gene
                mutated_value = max(ranges["min"], min(ranges["max"], mutated_value))
                child_genes[gene_name] = mutated_value
            else:
                child_genes[gene_name] = inherited_value
        
        child_energy = (CONFIG["INITIAL_ENERGY_MIN"] + CONFIG["INITIAL_ENERGY_MAX"]) / 2
        return Entity(child_x, child_y, child_energy, child_genes)

    def die(self):
        self.is_alive = False
        if CONFIG["DEBUG_LOGGING"]: print(f"Entity {self.id} died. Age: {self.age}, Energy: {self.energy:.1f}")

    def get_color(self):
        # Color based on energy (e.g., fades from blue to red as energy drops)
        # Or could be based on a gene, or fixed.
        # Simple: healthy vs low energy
        if self.energy < CONFIG["MIN_ENERGY_REPRODUCE"] / 2:
            return CONFIG["COLOR_ENTITY_LOW_ENERGY"]
        return CONFIG["COLOR_ENTITY_DEFAULT"]


class GameMap:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        # Using a set for food locations for O(1) average time complexity for add/remove/check
        self.food_locations = set()
        # Optional: grid to quickly find entities, for now entities are just in a list
        # self.entity_grid = [[[] for _ in range(height)] for _ in range(width)]


    def spawn_food_item(self):
        if len(self.food_locations) >= CONFIG["MAX_FOOD_ON_MAP"]:
            return False
        
        # Try a few times to find an empty spot
        for _ in range(10): # Max 10 attempts to find empty spot
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            if (x, y) not in self.food_locations: # Add more checks if entities occupy cells exclusively
                self.food_locations.add((x, y))
                return True
        return False

    def is_food_at(self, x, y):
        return (x, y) in self.food_locations

    def remove_food(self, x, y):
        if (x, y) in self.food_locations:
            self.food_locations.remove((x, y))
            return 1 # Amount of food removed (can be made variable)
        return 0

class Simulator:
    def __init__(self, config):
        self.config = config
        self.current_day = 0
        self.entities = []
        self.game_map = GameMap(config["MAP_WIDTH"], config["MAP_HEIGHT"])
        self._populate_initial_entities()
        self._spawn_initial_food()

    def _populate_initial_entities(self):
        Entity._next_id = 0 # Reset ID counter for new simulation
        for _ in range(self.config["INITIAL_POPULATION"]):
            x = random.randint(0, self.config["MAP_WIDTH"] - 1)
            y = random.randint(0, self.config["MAP_HEIGHT"] - 1)
            energy = random.uniform(self.config["INITIAL_ENERGY_MIN"], self.config["INITIAL_ENERGY_MAX"])
            self.entities.append(Entity(x, y, energy))

    def _spawn_initial_food(self):
        for _ in range(self.config["INITIAL_FOOD_ITEMS"]):
            self.game_map.spawn_food_item()

    def daily_cycle(self):
        self.current_day += 1
        if self.config["DEBUG_LOGGING"]: print(f"\n--- Day {self.current_day} ---")

        # 1. Spawn new food
        for _ in range(self.config["FOOD_SPAWN_PER_DAY"]):
            self.game_map.spawn_food_item()

        # 2. Entity actions (shuffle for fairness)
        random.shuffle(self.entities)
        for entity in self.entities:
            entity.daily_update(self.game_map)

        # 3. Reproduction
        newly_born = []
        potential_parents = [e for e in self.entities if e.can_reproduce()]
        random.shuffle(potential_parents)
        
        # Simple pairing: iterate and try to find a nearby partner
        used_parents = set()
        for i in range(len(potential_parents)):
            if len(self.entities) + len(newly_born) >= self.config["MAX_POPULATION"]:
                break
            if i in used_parents:
                continue

            parent1 = potential_parents[i]
            
            # Find a nearby partner (not already used as parent1 in this cycle)
            for j in range(i + 1, len(potential_parents)):
                if j in used_parents:
                    continue
                parent2 = potential_parents[j]

                dist_sq = (parent1.x - parent2.x)**2 + (parent1.y - parent2.y)**2
                if dist_sq <= self.config["REPRODUCTION_DISTANCE"]**2:
                    # Check individual reproduction rates
                    if random.random() < parent1.genes["reproduction_rate"] and \
                       random.random() < parent2.genes["reproduction_rate"]:
                        
                        # Spawn child near a parent
                        child_x = (parent1.x + parent2.x) // 2 + random.choice([-1,0,1])
                        child_y = (parent1.y + parent2.y) // 2 + random.choice([-1,0,1])
                        child_x = max(0, min(child_x, self.config["MAP_WIDTH"] - 1))
                        child_y = max(0, min(child_y, self.config["MAP_HEIGHT"] - 1))

                        child = parent1.reproduce(parent2, child_x, child_y)
                        if child:
                            newly_born.append(child)
                            used_parents.add(i)
                            used_parents.add(j)
                            if self.config["DEBUG_LOGGING"]: print(f"  Entities {parent1.id} & {parent2.id} reproduced child {child.id}")
                        break # parent1 found a mate
            
        self.entities.extend(newly_born)

        # 4. Remove dead entities
        self.entities = [e for e in self.entities if e.is_alive]

        # 5. Print summary periodically
        if self.current_day % self.config["PRINT_SUMMARY_EVERY_N_DAYS"] == 0:
            self.print_summary()
        
        return len(self.entities) > 0 # Return False if population extinct

    def print_summary(self):
        if not self.entities:
            print(f"Day {self.current_day}: POPULATION EXTINCT.")
            return

        print(f"\n--- SUMMARY DAY {self.current_day} ---")
        print(f"Population: {len(self.entities)}")
        print(f"Food on map: {len(self.game_map.food_locations)}")

        avg_genes = {}
        for gene_name in self.config["GENES_BASE"]:
            if self.entities:
                avg_genes[gene_name] = sum(e.genes[gene_name] for e in self.entities) / len(self.entities)
            else:
                avg_genes[gene_name] = 0
        
        print("Average Genes:")
        for name, avg_val in avg_genes.items():
            print(f"  - {name:<20}: {avg_val:.2f}")
        
        avg_age = sum(e.age for e in self.entities) / len(self.entities) if self.entities else 0
        avg_energy = sum(e.energy for e in self.entities) / len(self.entities) if self.entities else 0
        print(f"Average Age: {avg_age:.2f} days")
        print(f"Average Energy: {avg_energy:.2f}")


class Visualizer:
    def __init__(self, config, simulator):
        pygame.init()
        self.config = config
        self.simulator = simulator
        self.screen_width = config["MAP_WIDTH"] * config["CELL_SIZE"]
        self.screen_height = config["MAP_HEIGHT"] * config["CELL_SIZE"] + 50 # Extra space for HUD
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("EvoSimPy")
        self.font = pygame.font.SysFont(None, 24)
        self.clock = pygame.time.Clock()

    def draw_grid(self):
        if not self.config["SHOW_GRID"]: return
        for x in range(0, self.screen_width, self.config["CELL_SIZE"]):
            pygame.draw.line(self.screen, self.config["COLOR_GRID"], (x, 0), (x, self.screen_height - 50))
        for y in range(0, self.screen_height - 50, self.config["CELL_SIZE"]):
            pygame.draw.line(self.screen, self.config["COLOR_GRID"], (0, y), (self.screen_width, y))

    def draw_food(self):
        cs = self.config["CELL_SIZE"]
        for fx, fy in self.simulator.game_map.food_locations:
            rect = pygame.Rect(fx * cs, fy * cs, cs, cs)
            pygame.draw.ellipse(self.screen, self.config["COLOR_FOOD"], rect) # Ellipse for rounder food

    def draw_entities(self):
        cs = self.config["CELL_SIZE"]
        for entity in self.simulator.entities:
            if entity.is_alive:
                rect = pygame.Rect(entity.x * cs, entity.y * cs, cs, cs)
                # pygame.draw.rect(self.screen, entity.get_color(), rect)
                center_x = entity.x * cs + cs // 2
                center_y = entity.y * cs + cs // 2
                radius = cs // 2
                pygame.draw.circle(self.screen, entity.get_color(), (center_x, center_y), radius)
                
                # Optional: Draw perception radius
                # if self.config.get("DRAW_PERCEPTION_RADIUS", False):
                #    pygame.draw.circle(self.screen, (100,100,100), (center_x, center_y), int(entity.genes["perception_radius"] * cs), 1)


    def draw_hud(self):
        hud_y_start = self.config["MAP_HEIGHT"] * self.config["CELL_SIZE"]
        pygame.draw.rect(self.screen, (30,30,30), (0, hud_y_start, self.screen_width, 50))

        texts = [
            f"Day: {self.simulator.current_day}",
            f"Population: {len(self.simulator.entities)} / {self.config['MAX_POPULATION']}",
            f"Food: {len(self.simulator.game_map.food_locations)}",
            f"FPS: {self.clock.get_fps():.1f}"
        ]
        
        x_offset = 10
        for i, text_content in enumerate(texts):
            text_surface = self.font.render(text_content, True, (200, 200, 200))
            self.screen.blit(text_surface, (x_offset, hud_y_start + 5 + i * 15))
            x_offset += text_surface.get_width() + 20 # space out texts

    def run(self):
        running = True
        simulation_active = True
        last_sim_step_time = time.time()
        time_per_sim_day = 1.0 / self.config["SIM_DAYS_PER_PYGAME_SECOND"] if self.config["SIM_DAYS_PER_PYGAME_SECOND"] > 0 else 0

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if event.key == pygame.K_p: # Pause/Resume simulation
                        simulation_active = not simulation_active
                    if event.key == pygame.K_g: # Toggle grid
                        self.config["SHOW_GRID"] = not self.config["SHOW_GRID"]


            current_time = time.time()
            if simulation_active and (current_time - last_sim_step_time >= time_per_sim_day or time_per_sim_day == 0):
                if not self.simulator.daily_cycle(): # Run one simulation day
                    print("Population extinct. Simulation paused.")
                    simulation_active = False 
                last_sim_step_time = current_time
                if time_per_sim_day == 0: # if instantaneous, allow one step per frame
                    pass


            # Drawing
            self.screen.fill(self.config["COLOR_BACKGROUND"])
            self.draw_grid()
            self.draw_food()
            self.draw_entities()
            self.draw_hud()

            pygame.display.flip()
            self.clock.tick(self.config["FPS"])

        pygame.quit()

# --- Main Execution ---
if __name__ == "__main__":
    sim_instance = Simulator(CONFIG)
    visualizer = Visualizer(CONFIG, sim_instance)
    visualizer.run()
