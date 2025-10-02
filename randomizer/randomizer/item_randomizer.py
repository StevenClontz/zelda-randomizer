from typing import DefaultDict, List, Tuple, Iterable
from collections import defaultdict
from random import shuffle
import logging as log

from .constants import Direction, Item, LevelNum, Range, RoomNum, RoomType, WallType
from .data_table import DataTable
from .location import Location
from .flags import Flags


class ItemRandomizer():
  def __init__(self, data_table: DataTable, flags: Flags) -> None:
    self.data_table = data_table
    self.flags = flags
    self.item_shuffler = ItemShuffler(flags)
  
  def _GetOverworldItemLocation(self, item: Item):
    log.debug("_GetOverworldItemLocation for %s" % item)
    for cave_num in Range.VALID_CAVE_NUMBERS:
      for position_num in Range.VALID_CAVE_POSITION_NUMBERS:
        maybe_location = Location(cave_num=cave_num, position_num=position_num)
        if self.data_table.GetCaveItem(maybe_location) == item:
          log.debug("_GetOverworldItemLocation Found it at cave %d pos %d" % 
                      (maybe_location.GetCaveNum(),maybe_location.GetPositionNum()))
          return maybe_location
    log.warning("_GetOverworldItemLocation Couldn't find it :(")
    return None

  #WOOD_SWORD_LOCATION = Location.CavePosition(0, 2)
  WHITE_SWORD_LOCATION = Location.CavePosition(2, 2)
  MAGICAL_SWORD_LOCATION = Location.CavePosition(3, 2)
  LETTER_LOCATION = Location.CavePosition(8, 2)
  ARMOS_ITEM_LOCATION = Location.CavePosition(20, 2)
  COAST_ITEM_LOCATION = Location.CavePosition(21, 2)

  #Dict for item lookup
  DOWNGRADED_ITEM = {
    Item.BOMBS: Item.BOMBS,
    Item.WOOD_SWORD: Item.WOOD_SWORD,
    Item.WHITE_SWORD: Item.WOOD_SWORD,
    Item.MAGICAL_SWORD: Item.WOOD_SWORD,
    Item.NO_ITEM: Item.NO_ITEM,
    Item.BAIT: Item.BAIT,
    Item.RECORDER: Item.RECORDER,
    Item.BLUE_CANDLE: Item.BLUE_CANDLE,
    Item.RED_CANDLE: Item.BLUE_CANDLE,
    Item.WOOD_ARROWS: Item.WOOD_ARROWS,
    Item.SILVER_ARROWS: Item.WOOD_ARROWS,
    Item.BOW: Item.BOW,
    Item.MAGICAL_KEY: Item.MAGICAL_KEY,
    Item.RAFT: Item.RAFT,
    Item.LADDER: Item.LADDER,
    Item.TRIFORCE_OF_POWER: Item.TRIFORCE_OF_POWER,
    Item.FIVE_RUPEES: Item.FIVE_RUPEES,
    Item.WAND: Item.WAND,
    Item.BOOK: Item.BOOK,
    Item.BLUE_RING: Item.BLUE_RING,
    Item.RED_RING: Item.BLUE_RING,
    Item.POWER_BRACELET: Item.POWER_BRACELET,
    Item.LETTER: Item.LETTER,
    Item.COMPASS: Item.COMPASS,
    Item.MAP: Item.MAP,
    Item.RUPEE: Item.RUPEE,
    Item.KEY: Item.KEY,
    Item.HEART_CONTAINER: Item.HEART_CONTAINER,
    Item.TRIFORCE: Item.TRIFORCE,
    Item.MAGICAL_SHIELD: Item.MAGICAL_SHIELD,
    Item.WOODEN_BOOMERANG: Item.WOODEN_BOOMERANG,
    Item.MAGICAL_BOOMERANG: Item.MAGICAL_BOOMERANG,
    #Item.MAGICAL_BOOMERANG: Item.WOODEN_BOOMERANG, #Removed this b/c some don't consider magical boomerang to be an upgrade
    Item.BLUE_POTION: Item.BLUE_POTION,
    Item.RED_POTION: Item.RED_POTION,
    Item.SINGLE_HEART: Item.SINGLE_HEART,
    Item.OVERWORLD_NO_ITEM: Item.OVERWORLD_NO_ITEM,
    Item.BEAST_DEFEATED_VIRTUAL_ITEM: Item.BEAST_DEFEATED_VIRTUAL_ITEM,
    Item.KIDNAPPED_RESCUED_VIRTUAL_ITEM: Item.KIDNAPPED_RESCUED_VIRTUAL_ITEM
  }

  def _GetOverworldItemsToShuffle(self) -> List[Location]:
    items: List[Location] = []
    if self.flags.shuffle_white_sword:
      items.append(self.WHITE_SWORD_LOCATION)
    if self.flags.shuffle_magical_sword:
      items.append(self.MAGICAL_SWORD_LOCATION)
    if self.flags.shuffle_coast_item:
      items.append(self.COAST_ITEM_LOCATION)
    if self.flags.shuffle_armos_item:
      items.append(self.ARMOS_ITEM_LOCATION)
    if self.flags.shuffle_letter:
      items.append(self.LETTER_LOCATION)
    if self.flags.shuffle_shop_items:
      items.append(self._GetOverworldItemLocation(Item.WOOD_ARROWS))
      items.append(self._GetOverworldItemLocation(Item.BLUE_CANDLE))
      items.append(self._GetOverworldItemLocation(Item.BLUE_RING))
    return items

  def ResetState(self):
    self.item_shuffler.ResetState()

  def ReadItemsAndLocationsFromTable(self) -> None:
    for level_num in Range.VALID_LEVEL_NUMBERS:
      self._ReadItemsAndLocationsForUndergroundLevel(level_num)
    for location in self._GetOverworldItemsToShuffle():
      item_num = self.data_table.GetCaveItem(location)
      self.item_shuffler.AddLocationAndItem(location, item_num)

  def _ReadItemsAndLocationsForUndergroundLevel(self, level_num: LevelNum) -> None:
    log.debug("Reading staircase room data for level %d " % level_num)
    for staircase_room_num in self.data_table.GetLevelStaircaseRoomNumberList(level_num):
      self._ParseStaircaseRoom(level_num, staircase_room_num)
    level_start_room_num = self.data_table.GetLevelStartRoomNumber(level_num)
    log.debug("Traversing level %d.  Start room is %x. " % (level_num, level_start_room_num))
    self._ReadItemsAndLocationsRecursively(level_num, level_start_room_num)

  def _ParseStaircaseRoom(self, level_num: LevelNum, staircase_room_num: RoomNum) -> None:
    staircase_room = self.data_table.GetRoom(level_num, staircase_room_num)

    if staircase_room.GetType() == RoomType.ITEM_STAIRCASE:
      log.debug("  Found item staircase %x in L%d " % (staircase_room_num, level_num))
      assert staircase_room.GetLeftExit() == staircase_room.GetRightExit()
      self.data_table.GetRoom(
          level_num, staircase_room.GetLeftExit()).SetStaircaseRoomNumber(staircase_room_num)
    elif staircase_room.GetType() == RoomType.TRANSPORT_STAIRCASE:
      log.debug("  Found transport staircase %x in L%d " % (staircase_room_num, level_num))
      assert staircase_room.GetLeftExit() != staircase_room.GetRightExit()
      for associated_room_num in [staircase_room.GetLeftExit(), staircase_room.GetRightExit()]:
        self.data_table.GetRoom(level_num,
                                associated_room_num).SetStaircaseRoomNumber(staircase_room_num)
    else:
      log.fatal("Room in staircase room number list (%x) didn't have staircase type (%x)." %
                    (staircase_room_num, staircase_room.GetType()))

  def _ReadItemsAndLocationsRecursively(self, level_num: LevelNum, room_num: RoomNum) -> None:
    if room_num not in Range.VALID_ROOM_NUMBERS:
      return  # No escaping back into the overworld! :)
    room = self.data_table.GetRoom(level_num, room_num)
    if room.IsMarkedAsVisited():
      return
    room.MarkAsVisited()

    item = room.GetItem()
    if item not in [Item.NO_ITEM, Item.TRIFORCE_OF_POWER]:
        if not item.IsMinorDungeonItem() or self.flags.shuffle_minor_dungeon_items:
          self.item_shuffler.AddLocationAndItem(Location.LevelRoom(level_num, room_num), item)
 
    # Staircase cases (bad pun intended)
    if room.GetType() == RoomType.ITEM_STAIRCASE:
      return  # Dead end, no need to traverse further.
    elif room.GetType() == RoomType.TRANSPORT_STAIRCASE:
      for upstairs_room in [room.GetLeftExit(), room.GetRightExit()]:
        self._ReadItemsAndLocationsRecursively(level_num, upstairs_room)
      return
    # Regular (non-staircase) room case.  Check all four cardinal directions, plus "down".
    for direction in (Direction.WEST, Direction.NORTH, Direction.EAST, Direction.SOUTH):
      if room.GetWallType(direction) != WallType.SOLID_WALL:
        self._ReadItemsAndLocationsRecursively(level_num, RoomNum(room_num + direction))
    if room.HasStaircase():
      self._ReadItemsAndLocationsRecursively(level_num, room.GetStaircaseRoomNumber())

  def ShuffleItems(self) -> None:
    self.item_shuffler.ShuffleItems()

  def HasValidItemConfiguration(self) -> bool:
    return self.item_shuffler.HasValidItemConfiguration()

  def WriteItemsAndLocationsToTable(self) -> None:
    for (location, item_num) in self.item_shuffler.GetAllLocationAndItemData():
      if location.IsLevelRoom():
        self.data_table.SetRoomItem(location, item_num)
        if item_num == Item.TRIFORCE:
          self.data_table.UpdateTriforceLocation(location)
      elif location.IsCavePosition():
        self.data_table.SetCaveItem(location, item_num)


class ItemShuffler():
  def __init__(self, flags) -> None:
    self.flags = flags
    self.item_num_list: List[Item] = []
    self.per_level_item_location_lists: DefaultDict[LevelNum, List[Location]] = defaultdict(list)
    self.per_level_item_lists: DefaultDict[LevelNum, List[Item]] = defaultdict(list)

  def ResetState(self):
    self.item_num_list.clear()
    self.per_level_item_location_lists.clear()
    self.per_level_item_lists.clear()

  def AddLocationAndItem(self, location: Location, item_num: Item) -> None:
    if item_num == Item.TRIFORCE_OF_POWER:
      return
    level_num = location.GetLevelNum() if location.IsLevelRoom() else 10
    self.per_level_item_location_lists[level_num].append(location)
    log.debug("Location %d:  %s" %
              (len(self.per_level_item_location_lists[level_num]),location.ToString()))
    
    if item_num in [Item.MAP, Item.COMPASS, Item.TRIFORCE, Item.HEART_CONTAINER]:
      return
    #TO DONE: Dict Lookup has been applied
    if self.flags.progressive_items:
      item_num = ItemRandomizer.DOWNGRADED_ITEM[item_num]

    self.item_num_list.append(item_num)
    log.debug("Item #%d: %s. From %s" % (len(self.item_num_list), item_num, location.ToString()))

  def ShuffleItems(self) -> None:
    self.item_num_list.append(Item.HEART_CONTAINER)
    shuffle(self.item_num_list)
    for level_num in Range.VALID_LEVEL_AND_CAVE_NUMBERS:
      # Levels 1-8 get a tringle, map, and compass.  Level 9 only gets a map and compass.
      if level_num in Range.VALID_LEVEL_NUMBERS and self.flags.shuffle_minor_dungeon_items:
        self.per_level_item_lists[level_num] = [Item.MAP, Item.COMPASS]
      if level_num in range(1, 9):
        self.per_level_item_lists[level_num].append(Item.TRIFORCE)
        self.per_level_item_lists[level_num].append(Item.HEART_CONTAINER)

      num_locations_needing_an_item = len(self.per_level_item_location_lists[level_num]) - len(
          self.per_level_item_lists[level_num])

      while num_locations_needing_an_item > 0:
        self.per_level_item_lists[level_num].append(self.item_num_list.pop())
        num_locations_needing_an_item = num_locations_needing_an_item - 1

      if level_num in range(1, 10):  # Technically this could be for OW and caves too
        shuffle(self.per_level_item_lists[level_num])
    assert not self.item_num_list

  def HasValidItemConfiguration(self):
    for level_num in range(0, 11):
      for location, item in zip(self.per_level_item_location_lists[level_num],
                                    self.per_level_item_lists[level_num]):
        if (self.flags.progressive_items and location.IsShopPosition() and
            item.IsProgressiveUpgradeItem()):
            return False
        if location.IsCavePosition() and location.GetCaveNum() == 0x25 and item == Item.LADDER:
            return False
    return True   

  def GetAllLocationAndItemData(self) -> Iterable[Tuple[Location, Item]]:
    tbr = []
    for level_num in range(0, 11):
      for location, item_num in zip(self.per_level_item_location_lists[level_num],
                                    self.per_level_item_lists[level_num]):
        tbr.append((location, item_num))
    return tbr
