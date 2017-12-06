import sc2reader
import sys
from collections import defaultdict, deque
from os import path, listdir

class ActionTracker(object):
    name = 'ActionTracker'

    def handleInitGame(self, event, replay):
        for player in replay.players:
            player.action_count = 0
            player.action_list = []

    def incrementActionCount(self, event, replay, actionType):
        if event.player in replay.players:
            event.player.action_count += 1
            event.player.action_list.append((event.frame,actionType))

    def handleCommandEvent(self, event, replay):
        self.incrementActionCount(event, replay, 1)
    def handleSelectionEvent(self, event, replay):
        self.incrementActionCount(event, replay, 2)
    def handleControlGroupEvent(self, event, replay):
        self.incrementActionCount(event, replay, 3)

def nearest_hatchery(location, replay):
    hatcheries = [unit for unit in replay.active_units.values() if unit.is_building and unit.name in ['Hatchery', 'Lair', 'Hive']]
    closest = min(hatcheries, key=lambda h: (h.location[0]-location[0])**2 + (h.location[1]-location[1])**2)
    return closest.id

class InjectActionTracker(object):
    name = 'InjectActionTracker'
    def handleInitGame(self, event, replay):
        for human in replay.players:
            human.injectaction_frames = defaultdict(list)

    def handleCommandEvent(self, event, replay):
        if hasattr(event, 'ability_name') and event.ability_name == 'SpawnLarva':
            try:
                event.player.injectaction_frames[event.target_unit_id].append((event.frame,event.player.action_count))
            except Exception as e:
                print e

class LarvaTracker(object):
    name = 'LarvaTracker'

    def handleInitGame(self, event, replay):
        for human in replay.players:
            #human.larvapop_frames = defaultdict(deque)
            human.larvapop_frames = defaultdict(list)
            human.injectpop_frames = defaultdict(list)

    def handleTrackerEvent(self, event, replay):
        if event.name == 'UnitBornEvent' and event.unit.name == 'Larva' and event.frame > 0:
            hatchery_id = nearest_hatchery(event.location, replay)
            larvapop = event.unit_controller.larvapop_frames[hatchery_id]

            larvapop.append(event.frame)
            if len(larvapop) > 3 and larvapop[-1] == larvapop[-2]+4 and larvapop[-2] == larvapop[-3]+4 and larvapop[-3] == larvapop[-4]+4:
                self.process_injectpop(event, hatchery_id)

    def process_injectpop(self, event, hatchery_id):
        action_count = event.unit_controller.action_count
        event.unit_controller.injectpop_frames[hatchery_id].append((event.frame-12,action_count))

class UnitDeathTracker(object):
    name = 'UnitDeathTracker'

    def handleInitGame(self, event, replay):
        for human in replay.players:
            human.death_frames = []

    def handleTrackerEvent(self, event, replay):
        if event.name == 'UnitDiedEvent':
            unit = event.unit
            if unit.supply == 0 and unit.minerals == 0 and unit.vespene == 0:
                return
            unit.owner.death_frames.append((event.frame,unit.supply,unit.minerals,unit.vespene))

class CameraMovementTracker(object):
    name = 'CameraMovementTracker'

    def handleInitGame(self, event, replay):
        for human in replay.players:
            human.camera_movements = []

    def handleCameraEvent(self, event, replay):
        if event.player.is_human and not event.player.is_observer:
            event.player.camera_movements.append((event.frame,event.x,event.y))

#def inject_delays(replay):
#    out = []
#    sc2reader.engine.run(replay)
#    for player in replay.players:
#        for hatchid, pops in enumerate(player.injectpop_frames.values()):
#            for ndx, (prev_event, next_event) in enumerate(zip(pops,pops[1:])):
#                prev_frame, prev_actioncount = prev_event
#                next_frame, next_actioncount = next_event
#                out.append((player.pid, hatchid, next_frame - prev_frame, next_frame, next_actioncount - prev_actioncount))
#    return out

sc2reader.engine.register_plugin(ActionTracker())
sc2reader.engine.register_plugin(InjectActionTracker())
sc2reader.engine.register_plugin(LarvaTracker())
sc2reader.engine.register_plugin(UnitDeathTracker())
sc2reader.engine.register_plugin(CameraMovementTracker())

if __name__ == '__main__':
    indir = sys.argv[1]
    outdir = sys.argv[2]

    with open(outdir+'/injectPop.csv','w') as injectPopFile, open(outdir+'/injectAction.csv','w') as injectActionFile, \
            open(outdir+'/actionCount.csv','w') as allActionFile, open(outdir+'/unitDeaths.csv','w') as unitDeathFile, \
            open(outdir+'/replayMeta.csv','w') as replayMetaFile, open(outdir+'/camera.csv','w') as cameraFile:
        #injectFile.write('replayId,playerId,hatcheryId,injectionDelay,gameTime,actionsBetween\n')

        injectPopFile.write('replayId,playerId,hatcheryId,frameNum\n')
        injectActionFile.write('replayId,playerId,hatcheryId,frameNum\n')
        allActionFile.write('replayId,playerId,frameNum,actionType\n')
        unitDeathFile.write('replayId,playerId,frameNum,supply,minerals,vespene\n')
        replayMetaFile.write('replayId,isLadder,gameType,playerId,playerSid,playerUrl,toonHandle,toonId,league,isHuman,race,result\n')
        cameraFile.write('replayId,playerId,frameNum,x,y\n')

        for filename in [f for f in listdir(indir) if f.endswith('.SC2Replay')]:
            try:
                replayid = path.splitext(path.basename(filename))[0]
                print >> sys.stderr, 'Reading: %s'%(filename,)
                replay = sc2reader.load_replay(path.join(indir,filename))
                if replay.expansion != 'HotS':
                    continue
                sc2reader.engine.run(replay)
                #for e in delays:
                #    injectFile.write('%s,%d,%d,%d,%d,%d\n'%(replayid,e[0],e[1],e[2],e[3],e[4]))
                for player in replay.players:
                    for hatchid, frames in player.injectpop_frames.items():
                        for (frame,_) in frames:
                            injectPopFile.write('%s,%d,%d,%d\n'%(replayid,player.pid,hatchid,frame))
                    for hatchid, frames in player.injectaction_frames.items():
                        for (frame,_) in frames:
                            injectActionFile.write('%s,%d,%d,%d\n'%(replayid,player.pid,hatchid,frame))
                    for frame, supply, minerals, vespene in player.death_frames:
                        unitDeathFile.write('%s,%d,%d,%.1f,%d,%d\n'%(replayid,player.pid,frame,supply,minerals,vespene))
                    for frame, actionType in player.action_list:
                        allActionFile.write('%s,%d,%d,%d\n'%(replayid,player.pid,frame,actionType))
                    for frame, x, y in player.camera_movements:
                        cameraFile.write('%s,%d,%d,%d,%d\n'%(replayid,player.pid,frame,x,y))
                    player_url = getattr(player,'url','NO_URL_AVAILABLE')
                    player_league = getattr(player,'highest_league','NO_LEAGUE_AVAILABLE')
                    s = ('%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n'%(replayid,replay.is_ladder,replay.game_type,player.pid,player.sid,player_url,player.toon_handle,player.toon_id,player_league,player.is_human,player.play_race,player.result))
                    s = s.encode('utf8')
                    replayMetaFile.write(s)
            except UnicodeDecodeError as e:
                print >> sys.stderr, 'Something went wrong: %s: %s'%(filename, e)
            except AttributeError as e:
                print >> sys.stderr, 'Something went wrong: %s: %s'%(filename, e)
            replayMetaFile.flush()
