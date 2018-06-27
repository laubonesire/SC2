# Maximizing protoss economy early on

import sc2
import random
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import NEXUS, PROBE, PYLON, ASSIMILATOR, GATEWAY, CYBERNETICSCORE, ZEALOT, STALKER, FORGE


class MacroTossBot(sc2.BotAI):    
    async def on_step(self, iteration):
        await self.distribute_workers()
        await self.build_workers()
        await self.build_pylons()
        await self.build_assimilators()
        await self.build_infantry_buildings()
        await self.expand()
        await self.build_infantry_units()
        await self.attack()

    async def build_workers(self):
        for nexus in self.units(NEXUS).ready.noqueue:
            if self.can_afford(PROBE) and self.units(PROBE).amount < self.units(NEXUS).amount * 25:
                await self.do(nexus.train(PROBE))

    async def build_pylons(self):
        if self.supply_left < 5 * self.units(NEXUS).amount and not self.already_pending(PYLON):
            nexuses = self.units(NEXUS).ready
            if nexuses.exists:
                if self.can_afford(PYLON):
                    await self.build(PYLON, near=nexuses.first)

    async def build_assimilators(self):
        for nexus in self.units(NEXUS).ready:
            vespenes = self.state.vespene_geyser.closer_than(10.0, nexus)
            for vespene in vespenes:
                if self.units(PYLON).amount < 1:
                    break
                if self.units(ASSIMILATOR).amount / 2 >= self.units(NEXUS).amount:
                    break
                if not self.can_afford(ASSIMILATOR):
                    break
                worker = self.select_build_worker(vespene.position)
                if worker is None:
                    break
                if not self.units(ASSIMILATOR).closer_than(1.0, vespene).exists:
                    await self.do(worker.build(ASSIMILATOR, vespene))
    
    async def build_infantry_buildings(self):
        if self.units(PYLON).ready.exists:
            pylon = self.units(PYLON).ready.random

            if self.units(GATEWAY).exists and not self.units(CYBERNETICSCORE).exists:
                if self.can_afford(CYBERNETICSCORE) and not self.already_pending(CYBERNETICSCORE):
                    await self.build(CYBERNETICSCORE, near=pylon)
            
            elif len(self.units(GATEWAY)) < ((len(self.units(NEXUS)) * 3) - 2):
                if self.can_afford(GATEWAY):
                    await self.build(GATEWAY, near=pylon)
 
    async def expand(self):
        if self.units(NEXUS).amount < 4 and self.units(PROBE).amount > self.units(NEXUS).amount * 18 and self.can_afford(NEXUS) and not self.already_pending(NEXUS) and self.units(GATEWAY).amount > 0:
            await self.expand_now()

    async def build_forge(self):
        pylon = self.units(PYLON).ready
        if pylon.exists:
            if self.can_afford(FORGE):
                await self.build(FORGE, near=pylon)

    async def build_infantry_units(self):
        for gw in self.units(GATEWAY).ready.noqueue:
            if self.can_afford(STALKER) and self.supply_left > 0 and self.units(CYBERNETICSCORE).exists and self.units(STALKER).amount <= self.units(ZEALOT).amount * 2:
                await self.do(gw.train(STALKER))
            elif self.can_afford(ZEALOT) and self.supply_left > 0 and not self.units(CYBERNETICSCORE).ready:
                await self.do(gw.train(ZEALOT))
            elif self.can_afford(ZEALOT) and self.units(STALKER).amount >= self.units(ZEALOT).amount * 2:
                await self.do(gw.train(ZEALOT))

    def find_target(self, state):
        if len(self.known_enemy_units) > 0:
            return random.choice(self.known_enemy_units)
        elif len(self.known_enemy_structures) > 0:
            return random.choice(self.known_enemy_structures)
        else:
            return self.enemy_start_locations[0]
    
    async def attack(self):
        #{UNIT: [n to attack, n to defend]}
        army_comp = {ZEALOT: [8, 2],
                     STALKER: [16, 4]}
        for UNIT in army_comp:
            if self.units(UNIT).amount > army_comp[UNIT][0] and self.units(UNIT).amount > army_comp[UNIT][1]:
                for s in self.units(UNIT).idle:
                    await self.do(s.attack(self.find_target(self.state)))

            elif self.units(UNIT).amount > army_comp[UNIT][1]:
                if len(self.known_enemy_units) > 0:
                    for s in self.units(UNIT).idle:
                        await self.do(s.attack(random.choice(self.known_enemy_units)))

run_game(maps.get("AbyssalReefLE"), [
    Bot(Race.Protoss, MacroTossBot()),
    Computer(Race.Terran, Difficulty.Hard)
], realtime=False)