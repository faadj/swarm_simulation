# ==========================================
# model parameters & requirements (mini-project 1) Fahad Ali Jalil Student Number: 12502261
# ==========================================
# environment:
# - grid size: adjustable, defaults to 60x60.
# - nest: one single nest right in the middle of the grid.
# - food: finite and doesn't respawn. covers 10% to 15% of the map.
# - food clusters: split into 10 to 12 groups.
#
# swarm (the creatures):
# - swarm size: anywhere from 40 to 60 (we default to 50).
# - starting stats: full energy and safe temp.
# - perception: strictly local. they can only see their own stats, the nest, and food within 1 block.
# - actions: they can move, stay still, eat, or drop pheromones (stigmergy).
# - environment effects: they heat up outside, cool down inside the nest, and constantly lose energy.
# - death: they die if energy hits 0 or if they get too hot.
# - simulation end: it only stops when every single creature is dead.
# ==========================================
import mesa
from mesa.visualization import SolaraViz, make_space_component, make_plot_component
import random
import solara

# constants
E_MAX = 100
T_SAFE = 37
T_CRIT = 50
T_MIN = 30

# 1. agents

class Food(mesa.Agent):

    """agent representing finite, non renewable food."""

    def __init__(self, model):
        super().__init__(model)


class Pheromone(mesa.Agent):
    """agent representing a trace left by the ants"""

    def __init__(self, model):
        super().__init__(model)
        self.strength = 100

    def step(self):
        self.strength -= 5
        if self.strength <= 0:
            self.model.grid.remove_agent(self)
            self.model.agents.remove(self)


class CreatureAgent(mesa.Agent):
    """smarter agent using state machines, stigmergy, and momentum"""

    def __init__(self, model):
        super().__init__(model)
        self.energy = E_MAX
        self.temperature = T_SAFE
        self.is_alive = True

        # State Machine
        self.state = "RESTING"

        # Momentum variables
        self.explore_target = None
        self.explore_timer = 0

    def step(self):
        if not self.is_alive:
            return

        at_nest = (self.pos == self.model.nest_pos)

        # state transition
        if self.state == "RESTING":
            if self.temperature <= T_MIN:
                self.state = "EXPLORING"

        elif self.state == "EXPLORING":
            if self.temperature > 46:
                self.state = "RETURNING"

        elif self.state == "RETURNING":
            if at_nest:
                self.state = "RESTING"

        # Other enviornment drain
        if at_nest:
            self.temperature = max(T_MIN, self.temperature - 2.0)
        else:
            self.temperature += 0.5

        self.energy -= 1

        # death parameters
        if self.energy <= 0 or self.temperature >= T_CRIT:
            self.is_alive = False
            self.model.grid.remove_agent(self)
            self.model.agents.remove(self)
            return

        # action based on state
        if self.state == "RESTING":
            pass

        elif self.state == "RETURNING":
            possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
            if possible_steps:
                best_step = min(possible_steps,
                                key=lambda p: abs(p[0] - self.model.nest_pos[0]) + abs(p[1] - self.model.nest_pos[1]))
                self.model.grid.move_agent(self, best_step)
            self.energy -= 1

        elif self.state == "EXPLORING":
            neighbors = self.model.grid.get_neighbors(self.pos, moore=True, include_center=True, radius=1)

            food_here = [obj for obj in neighbors if isinstance(obj, Food) and obj.pos == self.pos]
            food_near = [obj for obj in neighbors if isinstance(obj, Food) and obj.pos != self.pos]
            pheromones_near = [obj for obj in neighbors if isinstance(obj, Pheromone) and obj.pos != self.pos]

            if len(food_here) > 0:
                food_item = food_here[0]
                self.energy = min(E_MAX, self.energy + 50)
                self.model.grid.remove_agent(food_item)
                self.model.agents.remove(food_item)
                self.model.drop_pheromone(self.pos)

            elif len(food_near) > 0:
                self.model.grid.move_agent(self, food_near[0].pos)
                self.energy -= 1

            elif len(pheromones_near) > 0:
                best_pheromone = max(pheromones_near, key=lambda p: p.strength)
                self.model.grid.move_agent(self, best_pheromone.pos)
                self.energy -= 1

            else:
                possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
                if possible_steps:
                    if self.explore_timer <= 0 or self.explore_target not in possible_steps:
                        self.explore_target = self.random.choice(possible_steps)
                        self.explore_timer = self.random.randint(5, 15)

                    dx = self.explore_target[0] - self.pos[0]
                    dy = self.explore_target[1] - self.pos[1]

                    self.model.grid.move_agent(self, self.explore_target)

                    next_x = min(max(self.explore_target[0] + dx, 0), self.model.grid.width - 1)
                    next_y = min(max(self.explore_target[1] + dy, 0), self.model.grid.height - 1)
                    self.explore_target = (next_x, next_y)

                    self.explore_timer -= 1
                self.energy -= 1



# 2. Model overview

class SwarmModel(mesa.Model):
    def __init__(self, num_agents=50, width=60, height=60, seed=None):
        super().__init__(seed=seed)
        self.num_agents = num_agents

        self.grid = mesa.space.MultiGrid(width, height, torus=False)
        self.nest_pos = (width // 2, height // 2)

        for _ in range(self.num_agents):
            a = CreatureAgent(self)
            self.grid.place_agent(a, self.nest_pos)

        self.generate_food_clusters(width, height)

        # Data collection
        # This tells Mesa to count up these statistics every single frame
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Alive": lambda m: sum(1 for a in m.agents if isinstance(a, CreatureAgent)),
                "Dead": lambda m: m.num_agents - sum(1 for a in m.agents if isinstance(a, CreatureAgent)),
                "Pheromones": lambda m: sum(1 for a in m.agents if isinstance(a, Pheromone))
            }
        )
        # Collect the initial state at step 0
        self.datacollector.collect(self)

    def drop_pheromone(self, pos):
        p = Pheromone(self)
        self.grid.place_agent(p, pos)

    def generate_food_clusters(self, width, height):
        target_food_cells = random.randint(360, 540)
        num_clusters = random.randint(10, 12)
        cells_per_cluster = target_food_cells // num_clusters

        for _ in range(num_clusters):
            cx, cy = random.randrange(width), random.randrange(height)
            for _ in range(cells_per_cluster):
                cx = min(max(cx + random.randint(-1, 1), 0), width - 1)
                cy = min(max(cy + random.randint(-1, 1), 0), height - 1)

                cell_contents = self.grid.get_cell_list_contents((cx, cy))
                if not any(isinstance(obj, Food) for obj in cell_contents):
                    f = Food(self)
                    self.grid.place_agent(f, (cx, cy))

    def step(self):
        self.agents.shuffle_do("step")

        # Save the data for this frame to draw the graphs
        self.datacollector.collect(self)

        creatures_alive = sum(1 for a in self.agents if isinstance(a, CreatureAgent))
        if creatures_alive == 0:
            self.running = False


# 3. (UI & GRAPHS)

def agent_portrayal(agent):
    # Dynamic Colors based on State Machine
    if isinstance(agent, CreatureAgent):
        if agent.state == "RESTING":
            return {"color": "blue", "marker": "o", "size": 50}
        elif agent.state == "EXPLORING":
            return {"color": "orange", "marker": "o", "size": 50}
        elif agent.state == "RETURNING":
            return {"color": "red", "marker": "o", "size": 50}

    elif isinstance(agent, Food):
        return {"color": "green", "marker": "s", "size": 40}

    elif isinstance(agent, Pheromone):
        size = max(10, (agent.strength / 100) * 40)
        return {"color": "purple", "marker": "s", "size": size}

    return {}


# legends
def legend_component(model):
    """Uses Solara Markdown to draw a legend above the grid."""
    return solara.Markdown('''
    ### Swarm Legend
    * **Blue Circle:** Resting in Nest (Cooling down)
    * **Orange Circle:** Exploring for Food
    * **Red Circle:** Returning to Nest (Heating up)
    * **Green Square:** Food Cluster
    * **Purple Square:** Pheromone Trail
    ''')


model_params = {
    "num_agents": 50,
    "width": 60,
    "height": 60
}

# This add the Legend and the two Plots into the Solara UI
page = SolaraViz(
    SwarmModel(num_agents=50, width=60, height=60),
    components=[
        legend_component,
        make_space_component(agent_portrayal),
        make_plot_component({"Alive": "blue", "Dead": "red"}),  # Graph 1: Population
        make_plot_component({"Pheromones": "purple"})  # Graph 2: Trails
    ],
    model_params=model_params,
    name="Swarm Survival Simulation"
)