local BtWQuests = BtWQuests
local Database = BtWQuests.Database

local EXPANSION_ID = 160

BtWQuests.Constant.Expansions.Forever = EXPANSION_ID
BtWQuests.Constant.Category.Forever = {
    ElwynnForest = 16001,
    BurningSteppes = 16003,
    Duskwood = 16004,
    HillsbradFoothills = 16005,
    RedridgeMountains = 16006,
    WesternPlaguelands = 16007,
    Wetlands = 16008,
    Darkshore = 16009,
    DustwallowMarsh = 16010,
    Zone16593 = 16011,
}
BtWQuests.Constant.Chain.Forever = {
    ElwynnForest = {},
    BurningSteppes = {},
    Duskwood = {},
    HillsbradFoothills = {},
    RedridgeMountains = {},
    WesternPlaguelands = {},
    Wetlands = {},
    Darkshore = {},
    DustwallowMarsh = {},
    Zone16593 = {},
}

local expansion = Database:AddExpansion(EXPANSION_ID, {
    name = "Forever",
})

expansion.name = "Forever"
expansion.image = {
    texture = "Interface\\AddOns\\BTWQuests\\UI-Expansion",
    texCoords = {0, 0.90625, 0, 0.8125},
}
