# Maximizing protoss economy early on

import sc2
import random
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import *


class MacroTossBot(sc2.BotAI):
    def __init__(self):
        self.warpgate_started = False
        self.warpgate_researched = False

    async def on_step(self, iteration):
        await self.distribute_workers()
        await self.build_workers()
        await self.chronoboost()
        await self.build_pylons()
        await self.build_assimilators()
        await self.build_infantry_buildings()
        await self.research_warpgate()
        await self.morph_warpgates()
        await self.expand()
#        await self.build_forge()
        await self.build_infantry_units()
        await self.warp_infantry_units()
        await self.attack()

    async def build_workers(self):
        for nexus in self.units(NEXUS).ready.noqueue:
            if self.can_afford(PROBE) and self.units(PROBE).amount < self.units(NEXUS).amount * 25:
                await self.do(nexus.train(PROBE))

    async def chronoboost(self):
        nexuses = self.units(NEXUS).ready
        for nexus in nexuses:
            abilities = await self.get_available_abilities(nexus)
            if AbilityId.EFFECT_CHRONOBOOSTENERGYCOST in abilities:
                await self.do(nexus(AbilityId(EFFECT_CHRONOBOOSTENERGYCOST), nexus))

    async def build_pylons(self):
        if self.supply_left < 5 * self.units(NEXUS).amount and not self.already_pending(PYLON):
            nexuses = self.units(NEXUS).ready
            if nexuses.exists:
                if self.can_afford(PYLON):
                    await self.build(PYLON, near=nexuses.random)

    async def build_assimilators(self):
        for nexus in self.units(NEXUS).ready:
            vespenes = self.state.vespene_geyser.closer_than(10.0, nexus)
            for vespene in vespenes:
                if self.units(PYLON).amount < 1:
                    break
                if self.vespene > 200:
                    break
                if self.units(ASSIMILATOR).amount / 2 >= self.units(NEXUS).amount:
                    break
                if not self.can_afford(ASSIMILATOR):
                    break
                if self.already_pending(ASSIMILATOR):
                    break
                worker = self.select_build_worker(vespene.position)
                if worker is None:
                    break
                if not self.units(ASSIMILATOR).closer_than(1.0, vespene).exists:
                    await self.do(worker.build(ASSIMILATOR, vespene))
    
    async def build_infantry_buildings(self):
        if self.units(PYLON).ready.exists:
            pylon = self.units(PYLON).ready.random
            if self.units(GATEWAY).ready.exists and not self.units(CYBERNETICSCORE).exists:
                if self.can_afford(CYBERNETICSCORE) and not self.already_pending(CYBERNETICSCORE):
                    await self.build(CYBERNETICSCORE, near=pylon)
            
            elif len(self.units(GATEWAY)) < ((len(self.units(NEXUS)) * 3) - 2):
                if self.can_afford(GATEWAY):
                    await self.build(GATEWAY, near=pylon)
 
    async def research_warpgate(self):
        if self.units(CYBERNETICSCORE).ready.exists and self.can_afford(RESEARCH_WARPGATE) and not self.warpgate_started:
            ccore = self.units(CYBERNETICSCORE).ready.first
            await self.do(ccore(RESEARCH_WARPGATE))
            self.warpgate_started = True

    async def morph_warpgates(self):
        for gateway in self.units(GATEWAY).ready:
            abilities = await self.get_available_abilities(gateway)
            if AbilityId.MORPH_WARPGATE in abilities and self.can_afford(AbilityId.MORPH_WARPGATE):
                await self.do(gateway(MORPH_WARPGATE))

    async def expand(self):
        if self.units(NEXUS).amount < 4 and self.units(PROBE).amount > self.units(NEXUS).amount * 18 and self.can_afford(NEXUS) and not self.already_pending(NEXUS) and self.units(GATEWAY).amount > 0:
            await self.expand_now()

    async def build_forge(self):
        if self.units(PYLON).ready.exists and not self.units(FORGE).exists:
            pylon = self.units(PYLON).ready.random
            if self.can_afford(FORGE) and len(self.units(GATEWAY)) > 2:
                await self.build(FORGE, near=pylon)

    async def build_infantry_units(self):
        for gw in self.units(GATEWAY).ready.noqueue:
            if self.units(ZEALOT).amount < 1 and self.can_afford(ZEALOT):
                await self.do(gw.train(ZEALOT))
            elif self.units(ZEALOT).amount > 0 and self.units(CYBERNETICSCORE).exists and self.can_afford(STALKER) and self.supply_left > 0 and self.units(STALKER).amount < 1:
                await self.do(gw.train(STALKER))
            elif self.can_afford(MORPH_WARPGATE):
                await self.do(gw(MORPH_WARPGATE))
    
    async def warp_infantry_units(self):
        pylons = self.units(PYLON).ready
        if pylons.exists:
            for wg in self.units(WARPGATE).ready:
                abilities = await self.get_available_abilities(wg)
                if AbilityId.WARPGATETRAIN_ZEALOT in abilities:
                    pos = pylons.closest_to(self.enemy_start_locations[0]).position.to2.random_on_distance(4)
                    placement = await self.find_placement(AbilityId.WARPGATETRAIN_STALKER, pos, placement_step=1)
                    if self.can_afford(STALKER) and self.units(STALKER).amount < self.units(ZEALOT).amount * 2:
                        await self.do(wg.warp_in(STALKER, placement))
                    elif self.can_afford(ZEALOT) and self.units(ZEALOT).amount <= self.units(STALKER).amount / 2:
                        await self.do(wg.warp_in(ZEALOT, placement))

    def find_target(self, state):
        if len(self.known_enemy_units) > 0:
            return random.choice(self.known_enemy_units)
        elif len(self.known_enemy_structures) > 0:
            return random.choice(self.known_enemy_structures)
        else:
            return self.enemy_start_locations[0]
    
    async def attack(self):
        #{UNIT: [n to attack, n to defend]}
        army_comp = {ZEALOT: [8, 1],
                     STALKER: [16, 2]}
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
    Computer(Race.Protoss, Difficulty.Hard)
    ], realtime=False)