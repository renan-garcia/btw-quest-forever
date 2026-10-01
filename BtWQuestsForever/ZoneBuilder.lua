local BtWQuests = BtWQuests
local Database = BtWQuests.Database

local Builder = {}
BtWQuests.ForeverBuilder = Builder

local function Column(questIDs)
    local items = {}
    for index, questID in ipairs(questIDs) do
        local item = {
            type = "quest",
            id = questID,
            x = 0,
        }
        if index < #questIDs then
            item.connections = { 1 }
        end
        items[index] = item
    end
    return items
end

local function ActiveAny(questIDs)
    local active = {}
    for index, questID in ipairs(questIDs) do
        active[index] = {
            type = "quest",
            id = questID,
            status = { "active", "completed" },
        }
    end
    return active
end

local function CompletedAll(questIDs)
    local completed = {}
    for index, questID in ipairs(questIDs) do
        completed[index] = {
            type = "quest",
            id = questID,
        }
    end
    return completed
end

function Builder.AddChain(chainID, categoryID, name, questIDs, rangeMin, rangeMax, requiredLevel, completeAll, faction, classID, raceID)
    local chain = {
        name = name,
        category = categoryID,
        expansion = BtWQuests.Constant.Expansions.Forever,
        range = { rangeMin, rangeMax },
        prerequisites = {
            {
                type = "level",
                level = requiredLevel,
            },
        },
        active = ActiveAny(questIDs),
        completed = completeAll and CompletedAll(questIDs) or {
            type = "quest",
            id = questIDs[#questIDs],
        },
        items = Column(questIDs),
    }
    local restrictions = {}
    if faction then
        restrictions[#restrictions + 1] = { type = "faction", id = faction }
    end
    if classID then
        restrictions[#restrictions + 1] = { type = "class", id = classID }
    end
    if raceID then
        restrictions[#restrictions + 1] = { type = "race", id = raceID }
    end
    if #restrictions == 1 then
        chain.restrictions = restrictions[1]
    elseif #restrictions > 1 then
        chain.restrictions = restrictions
    end
    Database:AddChain(chainID, chain)
end
