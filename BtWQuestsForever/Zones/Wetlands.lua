local L = BtWQuests.L
local Database = BtWQuests.Database
local EXPANSION_ID = BtWQuests.Constant.Expansions.Forever
local CATEGORY_ID = BtWQuests.Constant.Category.Forever.Wetlands
local Chain = BtWQuests.Constant.Chain.Forever.Wetlands
local AddChain = BtWQuests.ForeverBuilder.AddChain

Chain.ClassStormwindCity1250 = 161001

AddChain(Chain.ClassStormwindCity1250, CATEGORY_ID, L["StormwindCity_Wetlands_1250"], { 1250, 1264, 1265, 1266 }, 33, 36, 28, false, "Alliance", nil, nil)

Database:AddCategory(CATEGORY_ID, {
    name = BtWQuests.GetMapName(1437),
    expansion = EXPANSION_ID,
    buttonImage = {
        texture = 1851113,
        texCoords = {0, 1, 0, 1},
    },
    restrictions = {
        type = "faction",
        id = "Alliance",
    },
    items = {
        {
            type = "chain",
            id = Chain.ClassStormwindCity1250,
        },
    },
})

