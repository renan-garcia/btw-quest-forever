local L = BtWQuests.L
local Database = BtWQuests.Database
local EXPANSION_ID = BtWQuests.Constant.Expansions.Forever
local CATEGORY_ID = BtWQuests.Constant.Category.Forever.RedridgeMountains
local Chain = BtWQuests.Constant.Chain.Forever.RedridgeMountains
local AddChain = BtWQuests.ForeverBuilder.AddChain

Chain.ClassStormwindCityOtherAlliance = 160801

AddChain(Chain.ClassStormwindCityOtherAlliance, CATEGORY_ID, L["StormwindCity_RedridgeMountains_OtherAlliance"], { 1097 }, 15, 15, 9, true, "Alliance", nil, nil)

Database:AddCategory(CATEGORY_ID, {
    name = BtWQuests.GetMapName(1433),
    expansion = EXPANSION_ID,
    buttonImage = {
        texture = 1851085,
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

