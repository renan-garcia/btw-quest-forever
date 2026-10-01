local L = BtWQuests.L
local Database = BtWQuests.Database
local EXPANSION_ID = BtWQuests.Constant.Expansions.Forever
local CATEGORY_ID = BtWQuests.Constant.Category.Forever.Duskwood
local Chain = BtWQuests.Constant.Chain.Forever.Duskwood
local AddChain = BtWQuests.ForeverBuilder.AddChain

Chain.ClassStormwindCity1274 = 160501

AddChain(Chain.ClassStormwindCity1274, CATEGORY_ID, L["StormwindCity_Duskwood_1274"], { 1274, 1241, 1242, 1243, 1244, 1245, 1246, 1447, 1247, 1248, 1249 }, 28, 33, 28, false, "Alliance", nil, nil)

Database:AddCategory(CATEGORY_ID, {
    name = BtWQuests.GetMapName(1431),
    expansion = EXPANSION_ID,
    buttonImage = {
        texture = 1851098,
        texCoords = {0, 1, 0, 1},
    },
    restrictions = {
        type = "faction",
        id = "Alliance",
    },
    items = {
        {
            type = "chain",
            id = Chain.ClassStormwindCity1274,
        },
    },
})

