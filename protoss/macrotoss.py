# Maximizing protoss economy early on

import sc2
import random
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import NEXUS, PROBE, PYLON, ASSIMILATOR, GATEWAY, CYBERNETICSCORE, ZEALOT, STALKER




class MacroToss(sc2.BotAI):
    stance = "Macro"
    
    async def on_step(self, iteration):
        await self.select_stance()
        await self.distribute_workers()
        await self.build_workers()
        await self.build_pylons()
        await self.build_assimilators()
        await self.build_infantry_buildings()
        await self.expand()
        await self.build_infantry_units()
        await self.attack()

    async def select_stance(self):
        if self.known_enemy_units.amount < 1:
            self.stance = "Macro"
        if self.known_enemy_units.amount > 0:
            self.stance = "Defensive"
        if self.units(STALKER).amount > self.known_enemy_units.amount and self.units(STALKER).amount > 8:
            self.stance = "Offensive"
    
    async def build_workers(self):
        for nexus in self.units(NEXUS).ready.noqueue:
            if self.can_afford(PROBE) and self.units(PROBE).amount < 60:
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
            if self.units(NEXUS).amount < 2:
                if self.units(GATEWAY).ready.exists:
                    if not self.units(CYBERNETICSCORE):
                        if self.can_afford(CYBERNETICSCORE) and not self.already_pending(CYBERNETICSCORE):
                            await self.build(CYBERNETICSCORE, near=pylon)
                else:
                    if self.can_afford(GATEWAY) and self.units(GATEWAY).amount < 1:
                        await self.build(GATEWAY, near=pylon)
            else:
                if self.can_afford(GATEWAY) and self.units(GATEWAY).amount < self.units(NEXUS).amount * 3:
                    await self.build(GATEWAY, near=pylon)
 
    async def expand(self):
        if self.units(NEXUS).amount < 4 and self.units(PROBE).amount > self.units(NEXUS).amount * 18 and self.can_afford(NEXUS) and not self.already_pending(NEXUS) and self.units(GATEWAY).amount > 0:
            await self.expand_now()

    async def build_infantry_units(self):
        for gw in self.units(GATEWAY).ready.noqueue:
            if self.can_afford(STALKER) and self.supply_left > 0 and self.units(CYBERNETICSCORE).exists:
                await self.do(gw.train(STALKER))
            else:
                if self.can_afford(ZEALOT) and self.supply_left > 0:
                    await self.do(gw.train(ZEALOT))
    
    async def attack(self):
        if self.stance == "Offensive":
            for s in self.units(STALKER).idle:
                await self.do(s.attack(random.choice(self.known_enemy_units)))

run_game(maps.get("AbyssalReefLE"), [
    Bot(Race.Protoss, MacroToss()),
    Computer(Race.Terran, Difficulty.Easy)
], realtime=False)