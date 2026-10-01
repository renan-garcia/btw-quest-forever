local L = BtWQuests.L
local Database = BtWQuests.Database
local EXPANSION_ID = BtWQuests.Constant.Expansions.Forever
local CATEGORY_ID = BtWQuests.Constant.Category.Forever.BurningSteppes
local Chain = BtWQuests.Constant.Chain.Forever.BurningSteppes
local AddChain = BtWQuests.ForeverBuilder.AddChain

Chain.ClassStormwindCityOtherAlliance = 160401

AddChain(Chain.ClassStormwindCityOtherAlliance, CATEGORY_ID, L["StormwindCity_BurningSteppes_OtherAlliance"], { 6402 }, 60, 60, 50, true, "Alliance", nil, nil)

Database:AddCategory(CATEGORY_ID, {
    name = BtWQuests.GetMapName(1428),
    expansion = EXPANSION_ID,
    buttonImage = {
        texture = 1851095,
        texCoords = {0, 1, 0, 1},
    },
    restrictions = {
        type = "faction",
        id = "Alliance",
    },
    items = {
        {
            type = "chain",
            id = Chain.ClassStormwindCityOtherAlliance,
        },
    },
})

